import uuid

from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.products.models import Product

VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELED],
    OrderStatus.CONFIRMED: [OrderStatus.SEPARATED, OrderStatus.CANCELED],
    OrderStatus.SEPARATED: [OrderStatus.SHIPPED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
}


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    idempotency_key = serializers.CharField(max_length=255)
    items = OrderItemInputSerializer(many=True)
    observations = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        customer_id = attrs["customer_id"]
        items = attrs["items"]

        try:
            customer = Customer.objects.get(id=customer_id, is_active=True)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Cliente inativo ou inexistente.")

        if not items:
            raise serializers.ValidationError("Pedido sem items selecionados.")

        attrs["customer"] = customer
        return attrs

    def create(self, validated_data):
        customer = validated_data["customer"]
        items = validated_data["items"]
        idempotency_key = validated_data["idempotency_key"]
        observations = validated_data.get("observations", "")

        existing = Order.objects.filter(idempotency_key=idempotency_key).first()

        if existing:
            return existing

        with transaction.atomic():

            products_map = {}

            for item in items:
                product = Product.objects.select_for_update().get(
                    id=item["product_id"], is_active=True
                )

                if product.stock_quantity < item["quantity"]:
                    raise serializers.ValidationError(
                        f"Estoque insuficiente para o produto: {product.name}"
                    )

                products_map[product.id] = product

            order = Order.objects.create(
                order_number=str(uuid.uuid4()).replace("-", "")[:12],
                customer=customer,
                total_amount=0,
                idempotency_key=idempotency_key,
                observations=observations,
            )

            total = 0

            for item in items:
                product = products_map[item["product_id"]]
                quantity = item["quantity"]
                unit_price = product.price
                subtotal = unit_price * quantity

                Product.objects.filter(id=product.id).update(
                    stock_quantity=F("stock_quantity") - quantity
                )

                OrderItem.objects.create(
                    id=uuid.uuid4(),
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )

                total += subtotal

            order.total_amount = total
            order.save(update_fields=["total_amount"])

            return order


class OrderItemOutputSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "status",
            "total_amount",
            "observations",
            "created_at",
        ]


class OrderStatusHistoryOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "previous_status",
            "new_status",
            "changed_by",
            "reason",
            "created_at",
        ]


class OrderStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=OrderStatus.choices)
    changed_by = serializers.CharField(required=False, default="System")
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        order = self.context["order"]
        current_status = order.status
        new_status = attrs["new_status"]

        allowed = VALID_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            raise serializers.ValidationError("Transição de status inválida")

        attrs["previous_status"] = current_status
        return attrs

    def save(self):
        order = self.context["order"]
        new_status = self.validated_data["new_status"]
        previous_status = self.validated_data["previous_status"]
        reason = self.validated_data.get("reason", "")
        changed_by = self.validated_data["changed_by"]

        with transaction.atomic():
            order.status = new_status
            order.save(update_fields=["status"])

            OrderStatusHistory.objects.create(
                order=order,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                reason=reason,
            )

        return order
