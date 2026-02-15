from django.db import models
from apps.core.models import CoreModel


class Product(CoreModel):
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código interno"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Nome"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Preço"
    )
    stock_quantity = models.PositiveIntegerField(
        verbose_name="Quantidade em estoque"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Status"
    )

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        db_table = "products"
        indexes = [
            models.Index(fields=["stock_quantity"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return self.name

    def update_stock(self, quantity: int):
        self.stock_quantity = quantity
        self.save(update_fields=["stock_quantity"])
