import django_filters

from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    sku = django_filters.CharFilter(
        field_name="sku", lookup_expr="exact", label="Código SKU do produto"
    )
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="exact", label="Nome exato do produto"
    )
    name_like = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Nome do produto (LIKE)"
    )
    is_active = django_filters.BooleanFilter(
        field_name="is_active", label="Status do produto no sistema"
    )

    class Meta:
        model = Product
        fields = [
            "sku",
            "name",
            "is_active",
        ]
