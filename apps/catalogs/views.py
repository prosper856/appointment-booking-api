from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema  # <-- Added import
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import StandardPagination
from apps.base.permissions import IsProvider
from apps.providers.views import get_my_provider

from .models import Service
from .selectors import get_public_services
from .serializers import MyServiceSerializer, ServiceQuerySerializer, ServiceSerializer


# ---------- customers ----------

class ServiceListView(APIView):
    """Browse services. Optional: ?provider=<uuid>&search=<text>"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Services (Customer)"],
        parameters=[ServiceQuerySerializer],
        responses={200: ServiceSerializer(many=True)},
    )
    def get(self, request):
        query = ServiceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        services = get_public_services(
            provider_id=query.validated_data.get("provider"),
            search=query.validated_data.get("search"),
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(services, request, view=self)
        return paginator.get_paginated_response(ServiceSerializer(page, many=True).data)


class ServiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Services (Customer)"],
        responses={200: ServiceSerializer},
    )
    def get(self, request, pk):
        service = get_object_or_404(get_public_services(), pk=pk)
        return Response(ServiceSerializer(service).data)


# ---------- providers manage their own ----------

class MyServiceListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    @extend_schema(
        tags=["Services (Provider)"],
        responses={200: MyServiceSerializer(many=True)},
    )
    def get(self, request):
        provider = get_my_provider(request)
        services = Service.objects.filter(provider=provider)  # includes inactive ones
        return Response(MyServiceSerializer(services, many=True).data)

    @extend_schema(
        tags=["Services (Provider)"],
        request=MyServiceSerializer,
        responses={201: MyServiceSerializer},
    )
    def post(self, request):
        provider = get_my_provider(request)
        serializer = MyServiceSerializer(data=request.data, context={"provider": provider})
        serializer.is_valid(raise_exception=True)
        serializer.save(provider=provider)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyServiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    def _get(self, request, pk):
        provider = get_my_provider(request)
        # Filtering by provider means other providers' services return 404.
        return provider, get_object_or_404(Service, pk=pk, provider=provider)

    @extend_schema(
        tags=["Services (Provider)"],
        responses={200: MyServiceSerializer},
    )
    def get(self, request, pk):
        _, service = self._get(request, pk)
        return Response(MyServiceSerializer(service).data)

    @extend_schema(
        tags=["Services (Provider)"],
        request=MyServiceSerializer,
        responses={200: MyServiceSerializer},
    )
    def patch(self, request, pk):
        provider, service = self._get(request, pk)
        serializer = MyServiceSerializer(
            service, data=request.data, partial=True, context={"provider": provider}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["Services (Provider)"],
        responses={204: OpenApiResponse(description="Service deactivated successfully.")},
    )
    def delete(self, request, pk):
        # Deactivate instead of deleting, so booking history stays intact.
        _, service = self._get(request, pk)
        if service.is_active:
            service.is_active = False
            service.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)