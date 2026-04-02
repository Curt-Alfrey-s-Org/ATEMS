"""
API error handling and request correlation (Flask), aligned with rankings-bot patterns:
consistent JSON errors for /api/*, X-Request-ID on requests/responses, structured logging.
"""
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from flask import Response, g, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


def _request_id() -> str:
    return getattr(g, "request_id", None) or str(uuid.uuid4())


def register_api_error_handlers(app: "Flask") -> None:
    """Register before/after handlers and error handlers for API routes."""

    @app.before_request
    def _set_request_id() -> None:
        incoming = request.headers.get("X-Request-ID")
        if incoming and len(incoming) <= 128:
            g.request_id = incoming.strip()
        else:
            g.request_id = str(uuid.uuid4())

    @app.after_request
    def _add_request_id_header(response: Response) -> Response:
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers["X-Request-ID"] = rid
        return response

    @app.errorhandler(404)
    def _handle_404(e: HTTPException) -> Response | tuple:
        if request.path.startswith("/api/"):
            rid = _request_id()
            logger.info("API 404: %s %s", request.method, request.path, extra={"request_id": rid})
            return (
                jsonify(
                    error="not_found",
                    message="The requested API endpoint does not exist.",
                    request_id=rid,
                ),
                404,
            )
        return e

    @app.errorhandler(SQLAlchemyError)
    def _handle_sqlalchemy(e: SQLAlchemyError) -> Response | tuple:
        if request.path.startswith("/api/"):
            rid = _request_id()
            logger.exception("Database error on API route", extra={"request_id": rid})
            return (
                jsonify(
                    error="database_error",
                    message="A database error occurred.",
                    request_id=rid,
                ),
                500,
            )
        raise e

    @app.errorhandler(500)
    def _handle_500(e: HTTPException | Exception) -> Response | tuple:
        if request.path.startswith("/api/"):
            rid = _request_id()
            logger.exception("Unhandled error on API route", extra={"request_id": rid})
            show_detail = app.config.get("DEBUG", False)
            msg = str(e) if show_detail else "An unexpected error occurred."
            return (
                jsonify(
                    error="internal_error",
                    message=msg,
                    request_id=rid,
                ),
                500,
            )
        if isinstance(e, HTTPException):
            return e
        raise e
