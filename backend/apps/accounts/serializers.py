from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserRole

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "role": self.user.role,
        }
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    role = serializers.ChoiceField(
        choices=[UserRole.CUSTOMER, UserRole.MERCHANT_OWNER],
        default=UserRole.CUSTOMER,
    )

    class Meta:
        model = User
        fields = ("email", "phone", "password", "role")

    def validate_email(self, value: str) -> str:
        normalized = value.lower().strip()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get("phone", ""),
            role=validated_data.get("role", UserRole.CUSTOMER),
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "phone", "role", "is_active", "created_at")
        read_only_fields = ("id", "role", "is_active", "created_at")
