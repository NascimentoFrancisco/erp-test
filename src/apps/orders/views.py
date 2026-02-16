from django.db import transaction
from django.db.models import F
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderItemOutputSerializer,
    OrderStatusHistoryOutputSerializer,
    OrderStatusUpdateSerializer,
)
from apps.products.models import Product


@extend_schema_view(
    list=extend_schema(
        summary="Listagem de Pedidos",
        tags=["Pedidos"]
    ),
    retrieve=extend_schema(summary="Detalhar pedido", tags=["Pedidos"]),
    create=extend_schema(
        request=OrderCreateSerializer,
        responses=OrderDetailSerializer,
        summary="Criar pedido",
        tags=["Pedidos"],
    ),
    destroy=extend_schema(summary="Remover pedido", tags=["Pedidos"]),
)
class OrderViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin
):
    queryset = Order.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "update_status":
            return OrderStatusUpdateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        status_code = status.HTTP_201_CREATED
        if Order.objects.filter(
            idempotency_key=request.data.get("idempotency_key")
        ).count() > 1:
            status_code = status.HTTP_200_OK

        output = OrderDetailSerializer(order)
        return Response(output.data, status=status_code)

    @extend_schema(
        request=OrderStatusUpdateSerializer,
        responses=OrderDetailSerializer,
        summary="Atualizar status de pedido",
        tags=["Pedidos"],
    )
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, id=None):
        order = self.get_object()

        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={"order": order},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        responses=OrderItemOutputSerializer(many=True),
        summary="Listar itens do pedido",
        tags=["Pedidos"],
    )
    @action(detail=True, methods=["get"], url_path="items")
    def items(self, request, id=None):
        order = self.get_object()
        items = (
            OrderItem.objects
            .select_related("product")
            .filter(order=order)
            .order_by("created_at")
        )
        serializer = OrderItemOutputSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses=OrderStatusHistoryOutputSerializer(many=True),
        summary="Listar histórico de status do pedido",
        tags=["Pedidos"],
    )
    @action(detail=True, methods=["get"], url_path="status-history")
    def status_history(self, request, id=None):
        order = self.get_object()
        history = (
            OrderStatusHistory.objects
            .filter(order=order)
            .order_by("created_at")
        )
        serializer = OrderStatusHistoryOutputSerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise ValidationError(
                "Apenas pedidos PENDENTE ou CONFIRMADO podem ser cancelados."
            )

        with transaction.atomic():
            items = (
                OrderItem.objects
                .select_related("product")
                .select_for_update()
                .filter(order=order)
            )

            for item in items:
                Product.objects.filter(id=item.product.id).update(
                    stock_quantity=F("stock_quantity") + item.quantity
                )

            order.status = OrderStatus.CANCELED
            order.save(update_fields=["status"])

        return Response(status=status.HTTP_204_NO_CONTENT)
