from .models import Service


def get_public_services(*, provider_id=None, search=None):
    """Active services of active providers, for customers to browse."""
    qs = Service.objects.filter(is_active=True, provider__is_active=True).select_related("provider")
    if provider_id:
        qs = qs.filter(provider_id=provider_id)
    if search:
        qs = qs.filter(name__icontains=search)
    return qs