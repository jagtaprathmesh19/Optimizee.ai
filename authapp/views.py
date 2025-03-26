import logging
from django.contrib.auth import authenticate
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    ProfileSerializer,
)
from rest_framework.decorators import (
    permission_classes,
    authentication_classes,
)
from .models import AppUser
from rest_framework_simplejwt.authentication import JWTAuthentication


# Setup logger
logger = logging.getLogger(__name__)


class RegisterAPIView(APIView):
    """User Registration API"""

    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                profile, created = AppUser.objects.get_or_create(user=user)

                refresh = RefreshToken.for_user(user)

                logger.warning(
                    f"New user registered: {user.username} (Profile created: {created})"
                )

                return Response(
                    {
                        "message": "User registered successfully",
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                    },
                    status=status.HTTP_201_CREATED,
                )

            logger.warning(f"Registration failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during registration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginAPIView(APIView):
    """User Login API"""

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                username = serializer.validated_data["username"].strip()
                password = serializer.validated_data["password"].strip()
                user = authenticate(username=username, password=password)

                if user:
                    refresh = RefreshToken.for_user(user)
                    logger.info(f"User logged in: {username}")

                    return Response(
                        {
                            "access_token": str(refresh.access_token),
                            "refresh_token": str(refresh),
                        },
                        status=status.HTTP_200_OK,
                    )

                logger.warning(f"Failed login attempt for username: {username}")
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            logger.warning("Login attempt failed due to invalid input data")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during login"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutAPIView(APIView):
    """User Logout API"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                logger.warning("Logout failed: Refresh token not provided")
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User logged out successfully: {request.user.username}")

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfileView(APIView):
    """User Profile API"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = ProfileSerializer(user)
            logger.info(f"User profile fetched: {request.user.username}")

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching profile: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching the profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            user = request.user
            serializer = ProfileSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User profile updated: {request.user.username}")

                return Response(serializer.data, status=status.HTTP_200_OK)

            logger.warning(f"Profile update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while updating the profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile_page(request):
    """Render profile.html template"""
    return render(request, "user/profile.html")


def login_view(request):
    return render(request, "user/sign-in.html")


def register_view(request):
    return render(request, "user/sign-up.html")
