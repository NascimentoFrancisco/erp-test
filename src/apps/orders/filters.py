import django_filters

from apps.orders.models import Order, OrderStatus


class OrderFilter(django_filters.FilterSet):
    order_number = django_filters.CharFilter(
        field_name="order_number", lookup_expr="icontains", label="Número do pedido"
    )

    customer = django_filters.UUIDFilter(field_name="customer", label="ID do cliente")

    status = django_filters.ChoiceFilter(
        field_name="status", choices=OrderStatus.choices, label="Status do pedido"
    )

    class Meta:
        model = Order
        fields = [
            "order_number",
            "customer",
            "status",
        ]
