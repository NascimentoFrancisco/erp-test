import django_filters
from apps.customers.models import Customer


class CustomerFilter(django_filters.FilterSet):
    document = django_filters.CharFilter(label="CPF/CNPJ do cliente.")
    email = django_filters.CharFilter(label="E-mail doc cliente.")
    is_active = django_filters.BooleanFilter(label="Status do cliente do sistema.")

    class Meta:
        model = Customer
        fields = [
            "document",
            "email",
            "is_active",
        ]
