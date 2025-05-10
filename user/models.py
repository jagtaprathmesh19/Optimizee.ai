from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def default_expiration(category):
    """Sets default expiration date based on category."""
    if category in ["fruits", "vegetables"]:
        return timezone.now().date() + timezone.timedelta(days=5)  # Default 5 days
    return None


class FoodItem(models.Model):
    CATEGORY_CHOICES = [
        ("fruits", "Fruits"),
        ("vegetables", "Vegetables"),
        ("dairy", "Dairy"),
        ("meat", "Meat"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("fresh", "Fresh"),
        ("expiring_soon", "Expiring Soon"),
        ("expired", "Expired"),
        ("used", "Used"),
        ("donated", "Donated"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="food_items", default=1
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="fresh")
    expiration_date = models.DateField()
    image = models.ImageField(upload_to="food_images/", blank=True, null=True)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    def clean(self):
        """Ensure the expiration date is valid and update the status automatically."""
        if self.expiration_date < timezone.now().date():
            self.status = "expired"  # Mark as expired if the date has passed
        elif (self.expiration_date - timezone.now().date()).days <= 2:
            self.status = "expiring_soon"  # Mark as expiring soon if within 2 days
        super().clean()

    def update_status(self):
        """Automatically updates the status based on the expiration date."""
        if self.expiration_date:
            days_remaining = (self.expiration_date - timezone.now().date()).days
            if days_remaining < 0:
                self.status = "expired"
            elif days_remaining <= 2:
                self.status = "expiring_soon"
            else:
                self.status = "fresh"
        self.save()

    # def days_until_expiry(self):
    #     """Returns the number of days until expiration."""
    #     return (
    #         (self.expiration_date - timezone.now().date()).days
    #         if self.expiration_date
    #         else None
    #     )


class FoodItemPurchase(models.Model):
    MONTH_CHOICES = [
        (i, month)
        for i, month in enumerate(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            start=1,
        )
    ]

    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, related_name="purchases"
    )
    quantity = models.PositiveIntegerField(default=1)
    month_bought = models.IntegerField(choices=MONTH_CHOICES)
    year_bought = models.IntegerField(default=timezone.now().year)
    used_quantity = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )  # Food that was consumed
    wasted_quantity = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )  # Food that was wasted

    class Meta:
        ordering = ["-year_bought", "-month_bought"]

    def __str__(self):
        month = dict(self.MONTH_CHOICES).get(self.month_bought, "Unknown Month")
        return f"{self.food_item.name} - {self.quantity} purchased in {month} {self.year_bought}"

    def clean(self):
        """Ensure consumed and wasted quantities are within valid limits."""
        if self.used_quantity and self.used_quantity > self.quantity:
            raise ValidationError("Used quantity cannot exceed the purchased quantity.")
        if self.wasted_quantity and self.wasted_quantity > self.quantity:
            raise ValidationError(
                "Wasted quantity cannot exceed the purchased quantity."
            )
        super().clean()

    def calculate_wastage_cost(self):
        if self.amount_wasted and self.price_per_unit:
            return self.amount_wasted * self.price_per_unit
        return 0

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DetectedObject(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="detected_objects"
    )
    name = models.CharField(max_length=100)
    confidence = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} detected with {self.confidence * 100:.2f}% confidence"
