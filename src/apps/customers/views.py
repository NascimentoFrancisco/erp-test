from django.shortcuts import get_object_or_404
from rest_framework import (
    viewsets,
    status,
    response
)
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from apps.customers.models import Customer
from apps.customers.serializers import CustomerModelSerializer
from apps.customers.filters import CustomerFilter


@extend_schema_view(
    list=extend_schema(
        summary="Listagem de clientes",
        tags=["Clientes"]
    ),
    retrieve=extend_schema(summary="Detalhar cliente", tags=["Clientes"]),
    create=extend_schema(
        request=CustomerModelSerializer,
        responses=CustomerModelSerializer,
        summary="Criar cliente",
        tags=["Clientes"],
    ),
    partial_update=extend_schema(
        summary="Atualização parcial",
        request=CustomerModelSerializer,
        responses=CustomerModelSerializer,
        tags=["Clientes"]),
    destroy=extend_schema(summary="Remover cliente", tags=["Clientes"]),
)
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter

    def get_object(self) -> Customer:
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()
        customer.soft_delete()

        return response.Response(
            {},
            status=status.HTTP_204_NO_CONTENT
        )
