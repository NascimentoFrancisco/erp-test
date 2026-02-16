import uuid
from django.db import models
from django.db import IntegrityError
from apps.core.models import CoreModel


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    SEPARATED = "SEPARATED", "Separated"
    SHIPPED = "SHIPPED", "Shipped"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELED = "CANCELED", "Canceled"


class Order(CoreModel):
    order_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Número único do pedido"
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Cliente"
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="Status"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Valor total"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True
    )
    observations = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["deleted_at"]),
        ]

    def generate_order_number(self):
        return f"ORD-{uuid.uuid4().hex[:12].upper()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            for _ in range(5):
                self.order_number = self.generate_order_number()
                try:
                    return super().save(*args, **kwargs)
                except IntegrityError:
                    self.order_number = None
            raise IntegrityError("Could not generate unique order number.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Produto"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantidade"
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Preço initário"
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Subtotal"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
        ]


class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Pedido"
    )
    previous_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        verbose_name="Status anterir"
    )
    new_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        verbose_name="Novo status"
    )
    changed_by = models.CharField(
       max_length=255,
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["created_at"]),
        ]
