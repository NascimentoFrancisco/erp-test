from rest_framework import serializers
from apps.customers.models import Customer


class  CustomerModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "document",
            "email",
            "phone",
            "address",
            "is_active"
        ]
        read_only_fields = ["id", "is_active",]
