from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileView,
    login_view,
    register_view,
)

app_name = "authapp"  # Namespacing

urlpatterns = [
    path("api/signup/", RegisterAPIView.as_view(), name="api_signup"),
    path("api/login/", LoginAPIView.as_view(), name="api_login"),
    path("api/logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    # Frontend Login/Signup Pages
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
]
