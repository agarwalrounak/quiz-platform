from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")
        read_only_fields = ("id", "role")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, validators=[validate_password], style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        # Public registration always creates a plain user; admins are seeded /
        # created via createsuperuser, never through the public endpoint.
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            role=Role.USER,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Embeds role in the JWT and returns the user object alongside tokens."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
