"""
backend/services/sentiment.py

Sentiment analysis service for the Product Sentiment Analyzer project.

Responsibility (ONLY this):
    - Take review text (single string OR a pandas DataFrame of reviews) and
      classify it as positive / negative / neutral using VADER, producing a
      compound sentiment score between -1.0 and 1.0.

This module does NOT:
    - Read/write any files (that's scraper/clean_data.py's job)
    - Talk to Flask or MongoDB (that's backend/app.py and
      backend/services/database.py's job)
    - Know anything about the frontend

Per the Data Contract, the output of analyze_reviews_dataframe() should be
handed off to backend/services/database.py to be stored in MongoDB, and the
output of the /sentiment route (built on top of this data) is consumed by
the React frontend.
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# We create ONE analyzer instance at module load time instead of inside every
# function call. Building a SentimentIntensityAnalyzer has some setup cost
# (loading its internal lexicon), so re-creating it per-review would be
# wasteful when analyzing hundreds/thousands of reviews.
_analyzer = SentimentIntensityAnalyzer()

# Thresholds for turning VADER's compound score into a label.
# These are VADER's own recommended defaults (see VADER docs/paper).
# TODO: these thresholds can be tuned later if we find our review data
# skews too positive/negative with these defaults (e.g. sarcastic reviews).
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def analyze_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of a single piece of review text using VADER.

    Args:
        text (str): The review text to analyze. Expected to already be
            cleaned (per the Data Contract's "Cleaned review record"), but
            this function defends against None/empty/non-string input so it
            never crashes the caller.

    Returns:
        dict: {
            "sentiment": "positive" | "negative" | "neutral",
            "sentiment_score": float   # VADER compound score, -1.0 to 1.0
        }
    """
    # Guard against bad input (missing text, wrong type, etc.) rather than
    # letting VADER throw and crash whoever called us.
    if not isinstance(text, str) or text.strip() == "":
        return {"sentiment": "neutral", "sentiment_score": 0.0}

    try:
        # VADER's polarity_scores() returns a dict with 'neg', 'neu', 'pos',
        # and 'compound'. The 'compound' score is a single normalized value
        # (-1.0 = most negative, 1.0 = most positive) that's the standard
        # way to summarize overall sentiment, so that's what we use.
        scores = _analyzer.polarity_scores(text)
        compound_score = scores["compound"]
    except Exception as error:
        # If VADER somehow fails on a weird input, don't crash the whole
        # pipeline - fall back to a neutral, score-0 result and log it.
        print(f"[sentiment.py] Error analyzing text: {error}")
        return {"sentiment": "neutral", "sentiment_score": 0.0}

    sentiment_label = _score_to_label(compound_score)

    return {
        "sentiment": sentiment_label,
        "sentiment_score": round(compound_score, 4),
    }


def _score_to_label(compound_score: float) -> str:
    """
    Convert a VADER compound score into a sentiment label using our
    project-wide thresholds.

    Args:
        compound_score (float): VADER compound score, ranges -1.0 to 1.0.

    Returns:
        str: "positive", "negative", or "neutral".
    """
    if compound_score >= POSITIVE_THRESHOLD:
        return "positive"
    elif compound_score <= NEGATIVE_THRESHOLD:
        return "negative"
    else:
        return "neutral"


def analyze_reviews_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run sentiment analysis on every row of a reviews DataFrame.

    Takes a DataFrame that already has a 'review_text' column (i.e. the
    output of scraper/clean_data.py per the Data Contract) and returns a
    new DataFrame with two additional columns: 'sentiment' and
    'sentiment_score'.

    Args:
        df (pandas.DataFrame): Must contain a 'review_text' column.
            Expected (but not required) to also contain 'rating',
            'review_date', and 'reviewer_name' columns per the Data
            Contract's Cleaned review record shape - these are simply
            passed through untouched.

    Returns:
        pandas.DataFrame: A copy of the input DataFrame with two new
            columns added:
                - "sentiment" (str): "positive" | "negative" | "neutral"
                - "sentiment_score" (float): -1.0 to 1.0
            This matches the Data Contract's "Sentiment record" shape
            (once combined with the existing columns).
    """
    if "review_text" not in df.columns:
        # Fail loudly with a clear message rather than a confusing
        # KeyError deep inside pandas - this is a programmer error by
        # whoever called us with the wrong DataFrame shape.
        raise ValueError(
            "analyze_reviews_dataframe() requires a 'review_text' column, "
            f"but got columns: {list(df.columns)}"
        )

    # Work on a copy so we never mutate the caller's original DataFrame -
    # that could cause confusing bugs elsewhere in the pipeline.
    result_df = df.copy()

    sentiments = []
    scores = []

    for review_text in result_df["review_text"]:
        try:
            analysis_result = analyze_sentiment(review_text)
        except Exception as error:
            # Extra safety net: even though analyze_sentiment() already
            # handles its own errors internally, we don't want one bad row
            # to stop the whole DataFrame from being processed.
            print(f"[sentiment.py] Skipping row due to error: {error}")
            analysis_result = {"sentiment": "neutral", "sentiment_score": 0.0}

        sentiments.append(analysis_result["sentiment"])
        scores.append(analysis_result["sentiment_score"])

    result_df["sentiment"] = sentiments
    result_df["sentiment_score"] = scores

    return result_df