from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers
from .models import AppUser
import logging


logger = logging.getLogger("myapp")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying User information"""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")
        read_only_fields = ("username", "date_joined")


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["username"],
                    email=validated_data["email"],
                    password=validated_data["password"],
                )
                return user
        except IntegrityError:
            raise serializers.ValidationError(
                "A user with this username or email already exists."
            )

        except Exception as e:
            logger.error(f"User registration error: {str(e)}")
            raise serializers.ValidationError(f"Unexpected error: {str(e)}")


class AppUserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""

    user = UserSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    phone_number = serializers.CharField(required=True, max_length=15)

    class Meta:
        model = AppUser
        fields = [
            "id",
            "user",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "phone_number",
            "address",
            "allergies",
        ]

    def validate_phone_number(self, value):
        """Ensure phone number follows a valid international format."""
        import re

        pattern = r"^\+?1?\d{10,15}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid phone number.")
        return value

    def validate_address(self, value):
        """Clean up unnecessary spaces and format address properly."""
        return " ".join(value.split()).capitalize() if value else value

    def validate_allergies(self, value):
        """Format allergy list properly (capitalize & remove spaces)."""
        return value.strip().capitalize() if value else value

    def update(self, instance, validated_data):
        """Handle updating both User and AppUser fields."""
        # Extract User fields
        user_data = {}
        for field in ["first_name", "last_name"]:
            if f"user.{field}" in validated_data:
                user_data[field] = validated_data.pop(f"user.{field}")

        # Update User model if needed
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Update AppUser fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating profile information"""

    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)

    class Meta:
        model = AppUser
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "allergies",
        ]

    def validate_phone_number(self, value):
        import re

        pattern = r"^\+?1?\d{9,15}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Invalid phone number format. Please use format: +999999999 (10-15 digits)."
            )
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Custom update method to handle both User and AppUser updates.
        """

        # Update AppUser model fields
        # profile, created = AppUser.objects.update_or_create(user=instance)

        try:
            user_data = validated_data.pop("user", {})
            user = instance.user

            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

            # Update profile model fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            return instance

        except IntegrityError as e:
            raise serializers.ValidationError({e})
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            raise serializers.ValidationError(f"Error updating profile: {str(e)}")

        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        """Ensure username and password are provided."""
        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()

        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")

        # Check if input is email format
        if "@" in username:
            # Allow login with email
            try:
                user = User.objects.get(email=username)
                data["username"] = user.username
            except User.DoesNotExist:
                # Don't reveal if the email exists or not for security
                pass

        data["username"] = username  # Normalize username
        return data
