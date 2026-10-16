from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from apps.base.choices import AccountStatus, UserRole

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """What the API returns about a user."""

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone",
            "role", "status", "created_at",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """Only these fields can be changed through the profile endpoint."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    # Admin can never be chosen at registration.
    role = serializers.ChoiceField(
        choices=[(UserRole.CUSTOMER, "Customer"), (UserRole.PROVIDER, "Provider")],
        default=UserRole.CUSTOMER,
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "password", "role"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": False},
        }

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  # starts PENDING


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class VerifyOTPSerializer(EmailSerializer):
    otp = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].strip().lower(),
            password=attrs["password"],
        )
        if user is None:
            raise AuthenticationFailed("Invalid email or password.")

        if user.status == AccountStatus.PENDING:
            raise PermissionDenied("Please verify your email before logging in.")
        if user.status != AccountStatus.ACTIVE:
            raise PermissionDenied("This account is restricted. Please contact support.")

        attrs["user"] = user
        return attrs


class PasswordResetConfirmSerializer(VerifyOTPSerializer):
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value):
        validate_password(value)  # clear error for weak passwords, before the OTP is used
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()