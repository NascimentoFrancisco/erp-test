from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import response, status, viewsets
from rest_framework.decorators import action

from apps.products.filters import ProductFilter
from apps.products.models import Product
from apps.products.serializers import (
    ProductModelSerializer,
    ProductStockUpdateSerializer,
    ProductUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Listagem de produtos", tags=["Produtos"]),
    retrieve=extend_schema(summary="Detalhar produto", tags=["Produtos"]),
    partial_update=extend_schema(
        summary="Atualização parcial",
        request=ProductUpdateSerializer,
        responses=ProductModelSerializer,
        tags=["Produtos"],
    ),
    create=extend_schema(
        request=ProductModelSerializer,
        responses=ProductModelSerializer,
        summary="Criar produto",
        tags=["Produtos"],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_object(self) -> Product:
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        request=ProductStockUpdateSerializer,
        responses=ProductModelSerializer,
        summary="Atualizar estoque do produto",
        tags=["Produtos"],
    )
    @action(detail=True, methods=["patch"], url_path="update-stock")
    def update_stock(self, request, id=None):
        product = self.get_object()

        serializer = ProductStockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product.update_stock(serializer.validated_data["stock_quantity"])

        return response.Response(ProductModelSerializer(product).data, status=status.HTTP_200_OK)
