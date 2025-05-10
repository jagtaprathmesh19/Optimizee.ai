from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import datetime


class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )

    phone_number = models.CharField(
        max_length=15,
        validators=[phone_regex],
        blank=True,  # Consider if phone should be optional
    )

    address = models.TextField(verbose_name="User Address", blank=True, null=True)
    allergies = models.TextField(
        blank=True,
        null=True,
        help_text="List any food allergies or dietary restrictions",
    )

    # Additional useful fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "device_id")


class AuthenticationLevel(models.Model):
    LEVELS = (
        (1, "Basic - Password only"),
        (2, "Two-factor"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="auth_level"
    )
    current_level = models.IntegerField(choices=LEVELS, default=1)
    two_factor_verified = models.BooleanField(default=False)
    last_verification = models.DateTimeField(null=True, blank=True)
