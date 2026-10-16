
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework_simplejwt.tokens import RefreshToken

from apps.base.choices import AccountStatus
from apps.base.utils import generate_otp

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = getattr(settings, "OTP_EXPIRY_MINUTES", 15)
MAX_OTP_ATTEMPTS = 5


# ---------- OTP ----------

def set_user_otp(user, length: int = 6, reset_verified: bool = False) -> str:
    otp = generate_otp(length)
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.otp_attempts = 0

    fields = ["otp", "otp_created_at", "otp_attempts"]

    if reset_verified:
        user.otp_verified = False
        fields.append("otp_verified")

    user.save(update_fields=fields)
    return otp


def clear_user_otp(user) -> None:
    user.otp = None
    user.otp_created_at = None
    user.otp_attempts = 0
    user.save(update_fields=["otp", "otp_created_at", "otp_attempts"])


def verify_user_otp(user, otp: str) -> bool:
    if not user.otp or not user.otp_created_at:
        return False

    if user.otp_attempts >= MAX_OTP_ATTEMPTS:
        return False

    if timezone.now() > user.otp_created_at + timedelta(
        minutes=OTP_EXPIRY_MINUTES
    ):
        return False

    if not secrets.compare_digest(user.otp.encode(), otp.encode()):
        user.otp_attempts += 1
        user.save(update_fields=["otp_attempts"])
        return False

    user.otp_verified = True
    user.otp = None
    user.otp_created_at = None
    user.otp_attempts = 0
    user.save(
        update_fields=[
            "otp_verified",
            "otp",
            "otp_created_at",
            "otp_attempts",
        ]
    )
    return True


# ---------- Email ----------

def send_otp_email(user, otp: str, purpose: str) -> None:
    subject = f"{settings.APP_NAME}: your code for {purpose}"

    html_message = render_to_string(
        "emails/otp_email.html",
        {
            "user": user,
            "otp": otp,
            "purpose": purpose,
            "expiry": f"{OTP_EXPIRY_MINUTES} minutes",
            "app_name": settings.APP_NAME,
        },
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    message.attach_alternative(html_message, "text/html")
    message.send()


def send_verification_otp(user) -> bool:
    """Generate and email a verification code."""
    otp = set_user_otp(user, reset_verified=True)

    try:
        send_otp_email(user, otp, "email verification")
        return True
    except Exception:
        logger.exception("Failed to send verification email")
        return False


# ---------- Tokens ----------

def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ---------- Password reset ----------

def _get_active_user(email):
    User = get_user_model()

    return User.objects.get(
        email=email.lower().strip(),
        is_active=True,
        status=AccountStatus.ACTIVE,
    )


def initiate_password_reset(email) -> None:
    User = get_user_model()

    try:
        user = _get_active_user(email)
        otp = set_user_otp(user)
        send_otp_email(user, otp, "password reset")
    except User.DoesNotExist:
        pass
    except Exception:
        logger.exception("Password reset initiation failed")


def complete_password_reset(email, otp, new_password) -> bool:
    User = get_user_model()

    try:
        user = _get_active_user(email)
        validate_password(new_password, user)

        if not verify_user_otp(user, otp):
            return False

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return True

    except (User.DoesNotExist, ValidationError):
        return False
    except Exception:
        logger.exception("Password reset completion failed")
        return False
