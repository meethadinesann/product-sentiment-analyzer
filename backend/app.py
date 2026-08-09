"""
app.py

Entry point for the Flask backend of the Product Sentiment Analyzer and
Review Dashboard. This file is responsible ONLY for:
  - creating the Flask app
  - enabling CORS so the React frontend (on a different port) can call us
  - registering the review routes blueprint

All actual route logic lives in routes/review_routes.py, and all business
logic (scraping, cleaning, sentiment analysis, database access) lives in
the scraper/ and backend/services/ modules built by teammates.
"""

import os
import sys

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# --------------------------------------------------------------------------
# Make sure the project root is on sys.path.
# WHY: scraper/scrape_reviews.py and scraper/clean_data.py live at the
# project root (sibling to backend/), not inside the backend package.
# Without this, "from scraper.scrape_reviews import scrape_reviews" in
# review_routes.py would fail when app.py is run directly.
# --------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)  # go up one level from backend/
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Load environment variables from a .env file (never hardcode secrets here).
load_dotenv()

# Import the blueprint that holds our routes.
from routes.review_routes import review_bp  # noqa: E402  (import after sys.path fix)


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Parameters:
        None

    Returns:
        Flask: a configured Flask app instance with CORS enabled and the
        review routes blueprint registered.
    """
    app = Flask(__name__)

    # Enable CORS for all routes so the React dev server (e.g. localhost:3000
    # or localhost:5173) can call this API running on a different port.
    CORS(app)

    # Register the blueprint containing /reviews, /scrape, /sentiment routes.
    app.register_blueprint(review_bp)

    return app


# Create the app instance at module level so `flask run` / gunicorn can find it.
app = create_app()


if __name__ == "__main__":
    # Read host/port/debug from environment variables where possible, with
    # sensible defaults for local development.
    debug_mode = os.getenv("FLASK_DEBUG", "True") == "True"
    port = int(os.getenv("FLASK_PORT", "5000"))

    app.run(debug=debug_mode, port=port)