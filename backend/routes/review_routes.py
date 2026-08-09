"""
review_routes.py

Defines the API routes for the Product Sentiment Analyzer backend.

Routes implemented (must match the Data Contract exactly):
    GET  /reviews    -> {"reviews": [ <sentiment record>, ... ]}
    POST /scrape      -> {"status": "success" | "error", "message": string}
    GET  /sentiment    -> {"positive": int, "negative": int, "neutral": int,
                           "average_score": float,
                           "rating_distribution": {"1": int, ..., "5": int}}

This file does NOT reimplement scraping, cleaning, sentiment analysis, or
database logic. It only imports and calls those functions from the modules
built by teammates. If a function is missing or its signature does not
match what this module expects, a # TODO comment explains exactly what is
missing and a safe fallback is used so the server keeps running.
"""

from flask import Blueprint, jsonify

review_bp = Blueprint("review_bp", __name__)


# ---------------------------------------------------------------------------
# Imports from teammates' modules, each wrapped so a missing/incomplete
# module does not crash the whole Flask app during development.
# ---------------------------------------------------------------------------

try:
    from scraper.scrape_reviews import scrape_reviews
except ImportError:
    # TODO: scraper/scrape_reviews.py must expose a function
    # scrape_reviews() -> None (or a list of raw review dicts) that writes
    # to scraper/data/raw_reviews.csv per the Data Contract.
    def scrape_reviews():
        raise NotImplementedError(
            "scrape_reviews() is not implemented yet in scraper/scrape_reviews.py"
        )

try:
    from scraper.clean_data import clean_reviews
except ImportError:
    # TODO: scraper/clean_data.py must expose a function
    # clean_reviews() -> None (reads raw_reviews.csv, writes cleaned_reviews.csv)
    def clean_reviews():
        raise NotImplementedError(
            "clean_reviews() is not implemented yet in scraper/clean_data.py"
        )

try:
    from services.sentiment import analyze_reviews_dataframe
except ImportError:
    # TODO: backend/services/sentiment.py must expose a function
    # analyze_reviews_dataframe() -> list[dict] (sentiment records) that
    # reads scraper/data/cleaned_reviews.csv, runs VADER, and returns/saves
    # sentiment records matching the Data Contract.
    def analyze_reviews_dataframe():
        raise NotImplementedError(
            "analyze_reviews_dataframe() is not implemented yet in "
            "backend/services/sentiment.py"
        )

try:
    from services.database import get_reviews, insert_reviews
except ImportError:
    # TODO: backend/services/database.py must expose:
    #   get_reviews() -> list[dict]   (all sentiment records from MongoDB)
    #   insert_reviews(records: list[dict]) -> None  (inserts sentiment records)
    def get_reviews():
        raise NotImplementedError(
            "get_reviews() is not implemented yet in backend/services/database.py"
        )

    def insert_reviews(records):
        raise NotImplementedError(
            "insert_reviews() is not implemented yet in backend/services/database.py"
        )


@review_bp.route("/reviews", methods=["GET"])
def get_all_reviews():
    """
    Return all stored reviews with their sentiment data.

    Parameters:
        None (GET request, no body)

    Returns:
        JSON response shaped as {"reviews": [ <sentiment record>, ... ]}
        with HTTP 200 on success, or {"status": "error", "message": str}
        with HTTP 500 on failure.
    """
    try:
        reviews = get_reviews()
        return jsonify({"reviews": reviews}), 200
    except Exception as error:
        # Log clearly instead of letting the server crash.
        print(f"[ERROR] /reviews failed: {error}")
        return jsonify({"status": "error", "message": str(error)}), 500


@review_bp.route("/scrape", methods=["POST"])
def scrape_new_reviews():
    """
    Trigger the full pipeline: scrape -> clean -> analyze sentiment -> store.

    Parameters:
        None (POST request, no body expected)

    Returns:
        JSON response shaped as {"status": "success" | "error", "message": str}
        with HTTP 200 on success or HTTP 500 on failure.
    """
    try:
        # Step 1: scrape raw reviews from e-commerce site(s) into raw_reviews.csv
        scrape_reviews()

        # Step 2: clean the raw reviews into cleaned_reviews.csv
        clean_reviews()

        # Step 3: run sentiment analysis on cleaned reviews, get sentiment records
        sentiment_records = analyze_reviews_dataframe()

        # Step 4: store the sentiment records in the database
        insert_reviews(sentiment_records)

        return jsonify({
            "status": "success",
            "message": "Reviews scraped, analyzed, and stored successfully."
        }), 200

    except NotImplementedError as error:
        # A teammate's module isn't ready yet — this is not a real crash,
        # just missing dependency work. Report it clearly.
        print(f"[ERROR] /scrape failed - missing dependency: {error}")
        return jsonify({"status": "error", "message": str(error)}), 500

    except Exception as error:
        print(f"[ERROR] /scrape failed: {error}")
        return jsonify({"status": "error", "message": str(error)}), 500


@review_bp.route("/sentiment", methods=["GET"])
def get_sentiment_summary():
    """
    Aggregate sentiment counts, average sentiment score, and rating
    distribution across all stored reviews.

    Parameters:
        None (GET request, no body)

    Returns:
        JSON response shaped as:
            {
                "positive": int,
                "negative": int,
                "neutral": int,
                "average_score": float,
                "rating_distribution": {"1": int, "2": int, "3": int,
                                         "4": int, "5": int}
            }
        with HTTP 200 on success, or {"status": "error", "message": str}
        with HTTP 500 on failure.
    """
    try:
        reviews = get_reviews()

        summary = _build_sentiment_summary(reviews)
        return jsonify(summary), 200

    except Exception as error:
        print(f"[ERROR] /sentiment failed: {error}")
        return jsonify({"status": "error", "message": str(error)}), 500


def _build_sentiment_summary(reviews: list) -> dict:
    """
    Compute sentiment counts, average sentiment score, and rating
    distribution from a list of sentiment records.

    Parameters:
        reviews (list[dict]): list of sentiment records, each expected to
            have "sentiment" (str), "sentiment_score" (float), and
            "rating" (int) keys, per the Data Contract.

    Returns:
        dict: shaped as {"positive": int, "negative": int, "neutral": int,
              "average_score": float,
              "rating_distribution": {"1": int, ..., "5": int}}
    """
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0.0

    # Ratings 1-5, initialized to 0 so every key is always present.
    rating_distribution = {str(rating): 0 for rating in range(1, 6)}

    for review in reviews:
        # Use .get() with defaults so one malformed record doesn't crash
        # the whole summary calculation.
        sentiment = review.get("sentiment", "neutral")
        score = review.get("sentiment_score", 0.0)
        rating = review.get("rating")

        if sentiment == "positive":
            positive_count += 1
        elif sentiment == "negative":
            negative_count += 1
        else:
            neutral_count += 1

        total_score += score

        rating_key = str(rating)
        if rating_key in rating_distribution:
            rating_distribution[rating_key] += 1

    total_reviews = len(reviews)
    average_score = round(total_score / total_reviews, 4) if total_reviews > 0 else 0.0

    return {
        "positive": positive_count,
        "negative": negative_count,
        "neutral": neutral_count,
        "average_score": average_score,
        "rating_distribution": rating_distribution,
    }