"""
INCOME – Custom exception handler for consistent error responses.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger("income")


def custom_exception_handler(exc, context):
    """
    Returns JSON in the shape:
    { "success": false, "error": "...", "details": {...} }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": _get_error_message(response.data),
            "details": response.data,
            "status_code": response.status_code,
        }
        response.data = error_data
    else:
        logger.exception("Unhandled exception in view: %s", context.get("view"))
        response = Response(
            {
                "success": False,
                "error": "An internal server error occurred.",
                "status_code": 500,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_message(data) -> str:
    if isinstance(data, dict):
        for key in ("detail", "non_field_errors", "error"):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        # Return first field error
        for key, val in data.items():
            msg = str(val[0]) if isinstance(val, list) else str(val)
            return f"{key}: {msg}"
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
