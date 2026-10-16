import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


def _send_email(user, title, message) -> None:
    try:
        html = render_to_string(
            "emails/notification_email.html",
            {"user": user, "title": title, "message": message, "app_name": settings.APP_NAME},
        )
        email = EmailMessage(
            subject=f"{settings.APP_NAME}: {title}",
            body=html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.content_subtype = "html"
        email.send()
    except Exception:
        logger.exception("Failed to send notification email to %s", user.pk)


def notify(*, user, kind, title, message, related_model="", related_id=None, send_email=True):
    notification = Notification.objects.create(
        user=user, kind=kind, title=title, message=message,
        related_model=related_model, related_id=related_id,
    )
    if send_email:
        _send_email(user, title, message)
    return notification


def mark_read(*, user, pk):
    updated = Notification.objects.filter(user=user, pk=pk, is_read=False).update(
        is_read=True, read_at=timezone.now(), updated_at=timezone.now()
    )
    return updated


def mark_all_read(*, user) -> int:
    now = timezone.now()
    return Notification.objects.filter(user=user, is_read=False).update(
        is_read=True, read_at=now, updated_at=now
    )