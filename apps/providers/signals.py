from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.base.choices import UserRole

from .models import Provider


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_provider_profile(sender, instance, **kwargs):
    if instance.role == UserRole.PROVIDER:
        Provider.objects.get_or_create(
            user=instance,
            defaults={"business_name": instance.get_full_name() or instance.email},
        )