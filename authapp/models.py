from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        default="+911234567890",
    )
    address = models.TextField(verbose_name="User Address", blank=True, null=True)
    allergies = models.TextField(
        blank=True,
        null=True,
        help_text="List any food allergies or dietary restrictions",
    )

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
