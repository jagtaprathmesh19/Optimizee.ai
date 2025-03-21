from django.db import models


class FoodDonation(models.Model):
    FOOD_CATEGORIES = [
        ("Vegetarian", "Vegetarian"),
        ("Non-Vegetarian", "Non-Vegetarian"),
        ("Vegan", "Vegan"),
        ("Dessert", "Dessert"),
        ("Other", "Other"),
    ]

    food_name = models.CharField(max_length=250)
    quantity = models.IntegerField(
        help_text="Quantity in serving or weight (e.g; 1k.g.)"
    )
    category = models.CharField(max_length=50, choices=FOOD_CATEGORIES)
    expiry_date = models.DateField()
    location = models.CharField(max_length=250)
    food_image = models.ImageField(upload_to="food_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_name} - {self.quantity} units/kg"
