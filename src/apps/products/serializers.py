from rest_framework import serializers

from apps.products.models import Product


class ProductModelSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "price",
            "stock_quantity",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProductUpdateSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProductStockUpdateSerializer(serializers.Serializer):
    stock_quantity = serializers.IntegerField(min_value=0)
