from django.db import models

from apps.core.models import CoreModel
from apps.core.validators import validate_document


class Customer(CoreModel):
    name = models.CharField(verbose_name="Nome", max_length=255)
    document = models.CharField(
        verbose_name="CPF/CNPJ", max_length=18, unique=True, validators=[validate_document]
    )
    email = models.EmailField(verbose_name="E-mail", db_index=True, unique=True)
    phone = models.CharField(verbose_name="Telefone", max_length=20)
    address = models.TextField(verbose_name="Endereço")
    is_active = models.BooleanField(verbose_name="Status", default=True, db_index=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-created_at"]
        db_table = "customers"
        indexes = [
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return self.name
