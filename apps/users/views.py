from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.base.choices import AccountStatus

from .serializers import (
    EmailSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    VerifyOTPSerializer,
)
from .utils import (
    complete_password_reset,
    get_tokens_for_user,
    initiate_password_reset,
    send_verification_otp,
    verify_user_otp,
)

User = get_user_model()

GENERIC_OTP_ERROR = "Invalid or expired code."


class AuthThrottledView(APIView):
    """Base for public auth endpoints: open to anyone, rate limited."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=RegisterSerializer,
        responses={201: OpenApiResponse(description="Account created. A verification code was sent by email.")},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        email_sent = send_verification_otp(user)
        message = (
            "Account created. Check your email for the verification code."
            if email_sent
            else "Account created, but we couldn't send the code. Please request a new one."
        )
        return Response({"message": message}, status=status.HTTP_201_CREATED)


class VerifyEmailView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=VerifyOTPSerializer,
        responses={200: OpenApiResponse(description="Email verified. Returns the user and tokens.")},
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects.filter(
            email__iexact=email, status=AccountStatus.PENDING, is_active=True
        ).first()

        if user is None or not verify_user_otp(user, otp):
            return Response({"detail": GENERIC_OTP_ERROR}, status=status.HTTP_400_BAD_REQUEST)

        user.status = AccountStatus.ACTIVE
        user.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "message": "Email verified.",
                "user": UserSerializer(user).data,
                "tokens": get_tokens_for_user(user),
            }
        )


class ResendOTPView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=EmailSerializer,
        responses={200: OpenApiResponse(description="A new code is sent if the account needs verification.")},
    )
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            status=AccountStatus.PENDING,
            is_active=True,
        ).first()
        if user:
            send_verification_otp(user)

        # Same answer whether or not the account exists.
        return Response({"message": "If the account needs verification, a new code was sent."})


class LoginView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=LoginSerializer,
        responses={200: OpenApiResponse(description="Returns the user and tokens.")},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return Response(
            {"user": UserSerializer(user).data, "tokens": get_tokens_for_user(user)}
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        request=LogoutSerializer,
        responses={204: OpenApiResponse(description="Logged out. The refresh token is blacklisted.")},
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=EmailSerializer,
        responses={200: OpenApiResponse(description="A reset code is sent if the account exists.")},
    )
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        initiate_password_reset(serializer.validated_data["email"])

        return Response({"message": "If that account exists, a reset code was sent."})


class PasswordResetConfirmView(AuthThrottledView):
    @extend_schema(
        tags=["Auth"],
        request=PasswordResetConfirmSerializer,
        responses={200: OpenApiResponse(description="Password updated.")},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not complete_password_reset(data["email"], data["otp"], data["new_password"]):
            return Response({"detail": GENERIC_OTP_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Password updated. You can now log in."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Profile"], responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(tags=["Profile"], request=UserUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)