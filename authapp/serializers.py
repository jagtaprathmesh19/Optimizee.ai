from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import AppUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
            )
            # AppUser.objects.create(user=user)  # Create user profile
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create user: {str(e)}")


class AppUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AppUser
        fields = ["user", "phone_number", "address", "allergies"]


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer to combine User & AppUser data"""

    profile = AppUserSerializer()  # Nested serializer for additional profile fields

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "profile"]

    def update(self, instance, validated_data):
        """
        Custom update method to handle both User and AppUser updates.
        """
        profile_data = validated_data.pop("profile", {})

        # Update User model fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update AppUser model fields
        profile, created = AppUser.objects.get_or_create(user=instance)
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
