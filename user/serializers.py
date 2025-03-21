from rest_framework import serializers
from .models import FoodItem, DetectedObject


class FoodItemSerializer(serializers.ModelSerializer):
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = FoodItem
        fields = [
            "id",
            "name",
            "status",
            "expiration_date",
            "image",
            "category",
            "created_at",
            "updated_at",
            "days_until_expiry",
        ]

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()


class DetectedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectedObject
        fields = ["id", "name", "confidence", "timestamp", "user"]
        read_only_fields = ["id", "timestamp", "user"]
