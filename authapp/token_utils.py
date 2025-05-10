# Create token_utils.py file
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
    AuthenticationFailed,
)
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger("myapp")


def handle_token_error(error, user_identifier=None):
    """Centralized token error handling with improved logging"""

    error_msg = "Authentication failed"
    status_code = status.HTTP_401_UNAUTHORIZED
    log_level = logging.WARNING
    log_context = {"error_type": type(error).__name__}

    if user_identifier:
        log_context["user"] = user_identifier

    if isinstance(error, InvalidToken):
        error_msg = "Token is invalid"
        log_context["reason"] = "invalid_token"
    elif isinstance(error, TokenError) and "expired" in str(error).lower():
        error_msg = "Token has expired"
        log_context["reason"] = "token_expired"
    elif isinstance(error, AuthenticationFailed):
        error_msg = "Authentication failed"
        log_context["reason"] = "auth_failed"
    else:
        error_msg = "Token validation error"
        log_context["reason"] = "validation_error"

    # Log the error with context
    logger.log(log_level, f"Token error: {error_msg}", extra=log_context)

    return Response({"error": error_msg}, status=status_code)
