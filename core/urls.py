from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url="/swagger/", permanent=False)),  # optional
    path("admin/", admin.site.urls),

    path("api/", include("apps.users.urls")),
    path("api/", include("apps.providers.urls")),
    path("api/", include("apps.catalogs.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.complaints.urls")),
    path("api/", include("apps.notifications.urls")),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]