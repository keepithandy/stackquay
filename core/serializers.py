from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Record, User


def check_password(password, user):
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": exc.messages}) from exc


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "username", "email", "date_joined"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150, validators=User._meta.get_field("username").validators
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)

    def validate(self, attrs):
        attrs["email"] = attrs["email"].strip().lower()
        check_password(attrs["password"], User(username=attrs["username"], email=attrs["email"]))
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    user = UserSerializer()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class VerifySerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class ResetConfirmSerializer(VerifySerializer):
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ["id", "title", "body", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
