# Create token_service.py
import hashlib
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from datetime import datetime
import logging

logger = logging.getLogger("auth")


class TokenService:
    @staticmethod
    def create_tokens_for_user(user, device_id=None, ip_address=None):
        """Create tokens with appropriate claims and logging"""
        if not isinstance(user, User):
            raise ValueError("Invalid user object")

        refresh = RefreshToken.for_user(user)
        refresh["fingerprint"] = hashlib.sha256(
            f"{ip_address}:{device_id}".encode()
        ).hexdigest()

        # Add standard claims
        refresh["user_id"] = user.id
        refresh["username"] = user.username

        # Add optional claims
        if device_id:
            refresh["device_id"] = device_id
        if ip_address:
            refresh["ip"] = ip_address

        # Add timestamp
        refresh["created_at"] = datetime.now().timestamp()

        # Log token creation
        logger.info(
            f"Created tokens for user {user.username}",
            extra={
                "user_id": user.id,
                "device_id": device_id,
                "ip": ip_address,
                "token_jti": refresh.get("jti"),
            },
        )

        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @staticmethod
    def validate_token(token_string, token_type="access"):
        """Validate token and extract claims"""
        try:
            from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

            TokenClass = AccessToken if token_type == "access" else RefreshToken

            token = TokenClass(token_string)
            return {
                "valid": True,
                "payload": token.payload,
                "user_id": token.get("user_id"),
            }
        except Exception as e:
            logger.warning(
                f"Token validation failed: {str(e)}",
                extra={"error_type": type(e).__name__},
            )
            return {"valid": False, "error": str(e)}

    @staticmethod
    def blacklist_token(token_string):
        """Blacklist a refresh token"""
        try:
            token = RefreshToken(token_string)
            token.blacklist()

            # Log blacklisting
            logger.info("Token blacklisted", extra={"token_jti": token.get("jti")})
            return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False

    @staticmethod
    def create_tokens_with_auth_level(
        user, auth_level=1, device_id=None, ip_address=None
    ):
        """Create tokens with authentication level claims"""
        tokens = TokenService.create_tokens_for_user(user, device_id, ip_address)

        # Get raw token objects to modify
        refresh = RefreshToken(tokens["refresh"])

        # Add auth level claim
        refresh["auth_level"] = auth_level

        # Update tokens dictionary
        tokens["refresh"] = str(refresh)
        tokens["access"] = str(refresh.access_token)

        return tokens
