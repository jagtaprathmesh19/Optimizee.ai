from django.contrib import admin
from .models import FoodItem, FoodItemPurchase, DetectedObject

# Register your models here.
admin.site.register(FoodItemPurchase)
admin.site.register(FoodItem)


@admin.register(DetectedObject)
class DetectedObjectAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "confidence", "detected_at")
    search_fields = ("name", "user__username")
