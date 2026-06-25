"""Prometheus /metrics endpoint for ATEMS (Wave A monitoring scrape)."""

from flask import Blueprint, Response

metrics_bp = Blueprint("metrics", __name__)

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


@metrics_bp.route("/metrics")
def metrics():
    if not PROMETHEUS_AVAILABLE:
        return Response(
            "Prometheus client not available. Install prometheus-client.",
            status=503,
            mimetype="text/plain",
        )
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
