from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileView,
    RefreshTokenAPIView,
    StepUpAuthenticationView,
    login_view,
    register_view,
    profile_page,
)

app_name = "authapp"  # Namespacing

urlpatterns = [
    path("api/signup/", RegisterAPIView.as_view(), name="api_signup"),
    path("api/login/", LoginAPIView.as_view(), name="api_login"),
    path("api/logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("api/profile/", ProfileView.as_view(), name="api_profile"),
    path("api/token/refresh/", RefreshTokenAPIView.as_view(), name="token_refresh"),
    path("stepup-auth/", StepUpAuthenticationView.as_view(), name="stepup_auth"),
    # Frontend Login/Signup Pages
    path("profile/", profile_page, name="profile"),  # Render profile.html
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
]
