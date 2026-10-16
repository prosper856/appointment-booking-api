from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema  # <-- Added import
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import StandardPagination
from apps.base.permissions import IsProvider

from .models import Provider, WorkingHours
from .serializers import MyProviderSerializer, ProviderSerializer, WorkingHoursSerializer


def get_my_provider(request) -> Provider:
    provider = Provider.objects.filter(user=request.user).first()
    if provider is None:
        raise NotFound("You don't have a provider profile.")
    return provider


class ProviderListView(APIView):
    """Customers browse active providers. Optional ?search=name"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Providers"],
        responses={200: ProviderSerializer(many=True)},
    )
    def get(self, request):
        providers = Provider.objects.filter(is_active=True)
        search = request.query_params.get("search")
        if search:
            providers = providers.filter(business_name__icontains=search)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(providers, request, view=self)
        return paginator.get_paginated_response(ProviderSerializer(page, many=True).data)


class ProviderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Providers"],
        responses={200: ProviderSerializer},
    )
    def get(self, request, pk):
        provider = get_object_or_404(Provider, pk=pk, is_active=True)
        return Response(ProviderSerializer(provider).data)


class MyProviderView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    @extend_schema(
        tags=["My Provider"],
        responses={200: MyProviderSerializer},
    )
    def get(self, request):
        return Response(MyProviderSerializer(get_my_provider(request)).data)

    @extend_schema(
        tags=["My Provider"],
        request=MyProviderSerializer,
        responses={200: MyProviderSerializer},
    )
    def patch(self, request):
        provider = get_my_provider(request)
        serializer = MyProviderSerializer(provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MyWorkingHoursListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    @extend_schema(
        tags=["Working Hours"],
        responses={200: WorkingHoursSerializer(many=True)},
    )
    def get(self, request):
        provider = get_my_provider(request)
        hours = WorkingHours.objects.filter(provider=provider)
        return Response(WorkingHoursSerializer(hours, many=True).data)

    @extend_schema(
        tags=["Working Hours"],
        request=WorkingHoursSerializer,
        responses={201: WorkingHoursSerializer},
    )
    def post(self, request):
        provider = get_my_provider(request)
        serializer = WorkingHoursSerializer(data=request.data, context={"provider": provider})
        serializer.is_valid(raise_exception=True)
        serializer.save(provider=provider)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyWorkingHoursDetailView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    def _get_hours(self, request, pk):
        provider = get_my_provider(request)
        # Filtering by provider means other providers' hours return 404.
        return provider, get_object_or_404(WorkingHours, pk=pk, provider=provider)

    @extend_schema(
        tags=["Working Hours"],
        request=WorkingHoursSerializer,
        responses={200: WorkingHoursSerializer},
    )
    def patch(self, request, pk):
        provider, hours = self._get_hours(request, pk)
        serializer = WorkingHoursSerializer(
            hours, data=request.data, partial=True, context={"provider": provider}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["Working Hours"],
        responses={204: OpenApiResponse(description="Working hours deleted successfully.")},
    )
    def delete(self, request, pk):
        _, hours = self._get_hours(request, pk)
        hours.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)