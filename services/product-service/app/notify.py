import os
import logging
import requests

logger = logging.getLogger(__name__)

RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:8005")


def notify_recommendations():
    """
    Best-effort: tells the recommendation-service to re-embed changed products.
    Runs AFTER the admin's response has been sent (FastAPI BackgroundTasks), and
    swallows every error - an outage here must never block adding/editing a product.
    The next successful refresh (or the admin 'Refresh recommendations' button) catches up.
    """
    try:
        requests.post(
            f"{RECOMMENDATION_SERVICE_URL}/recommendations/refresh",
            headers={"x-internal-key": os.getenv("INTERNAL_API_KEY", "")},
            timeout=120,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not notify recommendation-service: %s", exc)
