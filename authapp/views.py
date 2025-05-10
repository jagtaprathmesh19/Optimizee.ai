import logging
import hashlib
import uuid
from datetime import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import AuthenticationFailed
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt


from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    AppUserSerializer,
)
from .models import AppUser, AuthenticationLevel
from .token_utils import handle_token_error
from .token_service import TokenService

from rest_framework.decorators import (
    permission_classes,
    authentication_classes,
)


# Setup logger
logger = logging.getLogger("myapp")


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def generate_device_id(request):
    """Generate a unique device identifier based on user agent and a salt"""
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    salt = str(uuid.uuid4())
    fingerprint = f"{user_agent}:{salt}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class RefreshRateThrottle(AnonRateThrottle):
    scope = "refresh"


@method_decorator(csrf_exempt, name="dispatch")
class RegisterAPIView(APIView):
    """User Registration API"""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    @transaction.atomic
    def post(self, request):
        try:
            logger.info(f"Registration request data: {request.data}")
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                profile, _ = AppUser.objects.get_or_create(user=user)

                logger.info(f"User created with ID: {user.id} {profile}")

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                logger.info(f"Tokens generated for user: {user.username}")

                response = Response(
                    {
                        "message": "User registered successfully",
                        "access_token": access_token,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )

                # Set refresh token as HttpOnly cookie (safer than sending in response body)
                response.set_cookie(
                    "refresh_token",
                    str(refresh),
                    httponly=True,
                    secure=True,  # Only over HTTPS
                    samesite="Strict",  # CSRF protection
                    max_age=86400 * 7,  # 7 days
                )

                return response

            logger.warning(f"Registration failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during registration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class LoginAPIView(APIView):
    """User Login API"""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                username = serializer.validated_data["username"].strip()
                password = serializer.validated_data["password"].strip()

                # Try to authenticate with email if username contains @
                if "@" in username:
                    try:
                        user_obj = User.objects.get(email=username)
                        username = user_obj.username
                    except User.DoesNotExist:
                        pass

                user = authenticate(username=username, password=password)

                if user:
                    device_id = generate_device_id(request)

                    # Get client IP
                    ip_address = get_client_ip(request)

                    # Use the service to create tokens
                    tokens = TokenService.create_tokens_for_user(
                        user, device_id=device_id, ip_address=ip_address
                    )

                    response = Response(
                        {
                            "access_token": tokens["access"],
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "email": user.email,
                            },
                        },
                        status=status.HTTP_200_OK,
                    )

                    # Set refresh token as HttpOnly cookie
                    response.set_cookie(
                        "refresh_token",
                        tokens["refresh"],
                        httponly=True,
                        secure=True,
                        samesite="Strict",
                        max_age=86400 * 7,  # 7 days
                    )

                    logger.info(f"User logged in: {user.username}")
                    return response

                logger.warning(f"Failed login attempt for username: {username}")
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during login"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class RefreshTokenAPIView(APIView):
    """API endpoint for refreshing access tokens"""

    throttle_classes = [RefreshRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get("refresh_token")

            if not refresh_token:
                logger.warning("Token refresh failed: No refresh token in cookie")
                return Response(
                    {"error": "No refresh token provided"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Verify and create new tokens
            refresh = RefreshToken(refresh_token)

            # Get user from the token
            user = refresh.get_user()
            if not user:
                logger.error("Failed to get user from refresh token")
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            access_token = str(refresh.access_token)

            response = Response(
                {"access_token": access_token}, status=status.HTTP_200_OK
            )

            # Check if token rotation is enabled
            from django.conf import settings

            rotate_refresh_tokens = getattr(settings, "SIMPLE_JWT", {}).get(
                "ROTATE_REFRESH_TOKENS", False
            )

            if rotate_refresh_tokens:
                # Generate new refresh token (token rotation for better security)
                new_refresh = RefreshToken.for_user(user)

                # Set new refresh token as HttpOnly cookie
                response.set_cookie(
                    "refresh_token",
                    str(new_refresh),
                    httponly=True,
                    secure=True,
                    samesite="Strict",
                    max_age=86400 * 7,  # 7 days
                )
                # Blacklist old token if blacklisting is enabled
                blacklist_after_rotation = getattr(settings, "SIMPLE_JWT", {}).get(
                    "BLACKLIST_AFTER_ROTATION", False
                )
                if blacklist_after_rotation:
                    try:
                        # Add the old token to the blacklist
                        refresh.blacklist()
                    except AttributeError:
                        pass

            return response

        except TokenError as e:
            response.delete_cookie("refresh_token")
            return handle_token_error(e)

        except Exception as e:
            logger.error(f"Err  or refreshing token: {str(e)}", exc_info=True)
            return Response(
                {"error": "Token refresh failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class LogoutAPIView(APIView):
    """User Logout API"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                jti = token.get("jti")
                token.blacklist()
                logger.info(
                    f"Token with JTI {jti} blacklisted for user: {request.user.username}"
                )
            else:
                logger.warning(f"Logout without refresh token: {request.user.username}")

            response = Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_205_RESET_CONTENT,
            )
            response.delete_cookie("refresh_token")
            return response
        except TokenError:
            # Even if token is invalid, we should clear it
            response = Response(
                {"message": "Logged out successfully"}, status=status.HTTP_200_OK
            )
            response.delete_cookie("refresh_token")
            return response

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class ProfileView(APIView):
    """User Profile API"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_profile_instance(self):
        """Get profile with existence check"""
        try:
            return AppUser.objects.get(user=self.request.user)
        except AppUser.DoesNotExist:
            logger.warning(
                f"Profile missing for user {self.request.user}, creating new profile"
            )
            return AppUser.objects.create(user=self.request.user)

    def get(self, request):
        try:
            request.user.refresh_from_db()
            profile = self.get_profile_instance()
            serializer = AppUserSerializer(profile)
            logger.info(f"Serialized Data: {serializer.data}")

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching profile: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching the profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @transaction.atomic
    def put(self, request):
        return self._update_profile(request, partial=False)

    @transaction.atomic
    def patch(self, request):
        """Partial update of user profile"""
        # Reuse the put method since we're already using partial=True
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial):
        try:
            profile = self.get_profile_instance()
            serializer = ProfileUpdateSerializer(
                profile, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            updated_profile = serializer.save()
            response_serializer = AppUserSerializer(updated_profile)
            logger.info(f"User profile updated: {request.user.username}")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except serializer.ValidationError as e:
            logger.warning(f"Profile validation error: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to update profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StepUpAuthenticationView(APIView):
    """View to raise the authentication level"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            auth_method = request.data.get("auth_method")
            verification_data = request.data.get("verification_data")

            # Get current auth level
            try:
                auth_level = AuthenticationLevel.objects.get(user=request.user)
            except AuthenticationLevel.DoesNotExist:
                auth_level = AuthenticationLevel.objects.create(user=request.user)

            # Verify based on method
            verified = False
            new_level = auth_level.current_level

            if auth_method == "two_factor":
                verified = self.verify_two_factor(request.user, verification_data)
                if verified:
                    new_level = max(new_level, 2)
                    auth_level.current_level = new_level
                    auth_level.two_factor_verified = True
                    auth_level.last_verification = timezone.now()
                    auth_level.save()

            elif auth_method == "biometric":
                # Implement your biometric verification logic
                verified = self.verify_biometric(request.user, verification_data)
                if verified:
                    new_level = max(new_level, 3)
                    auth_level.current_level = new_level
                    auth_level.biometric_verified = True
                    auth_level.last_verification = timezone.now()
                    auth_level.save()

            if verified:
                # Generate new tokens with higher auth level
                device_id = generate_device_id(request)
                ip_address = get_client_ip(request)

                tokens = TokenService.create_tokens_with_auth_level(
                    request.user,
                    auth_level=new_level,
                    device_id=device_id,
                    ip_address=ip_address,
                )

                response = Response(
                    {
                        "message": "Authentication level upgraded",
                        "auth_level": new_level,
                        "access_token": tokens["access"],
                    }
                )

                # Set new refresh token
                response.set_cookie(
                    "refresh_token",
                    tokens["refresh"],
                    httponly=True,
                    secure=True,
                    samesite="Strict",
                    max_age=86400 * 7,
                )

                return response
            else:
                return Response(
                    {"error": "Verification failed"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        except Exception as e:
            logger.error(f"Step-up authentication error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Authentication upgrade failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def verify_two_factor(self, user, verification_data):
        # Implement your 2FA verification logic
        # Just a placeholder example
        return True

    def verify_biometric(self, user, verification_data):
        # Implement your biometric verification logic
        # Just a placeholder example
        return True


@csrf_exempt
@never_cache
def profile_page(request):
    # Manually authenticate using JWT
    # jwt_auth = JWTAuthentication()
    # try:
    #     user_auth_tuple = jwt_auth.authenticate(request)
    #     if user_auth_tuple is None:
    #         raise AuthenticationFailed("No valid JWT found")
    #     request.user, _ = user_auth_tuple
    # except Exception:
    #     # Redirect to login or show error
    #     from django.shortcuts import redirect

    #     return redirect("authapp:login")
    return render(request, "user/profile.html")


def login_view(request):
    return render(request, "user/sign-in.html")


def register_view(request):
    return render(request, "user/sign-up.html")
