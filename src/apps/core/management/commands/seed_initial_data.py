from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.products.models import Product


class Command(BaseCommand):
    help = "Create idempotent initial development seed data."

    def handle(self, *args, **options):
        customer = self._seed_customer()
        products = self._seed_products()
        self._seed_order(customer, products)
        self.stdout.write(self.style.SUCCESS("Initial seed executed successfully."))

    def _seed_customer(self):
        customer, _ = Customer.objects.update_or_create(
            document="65998838009",
            defaults={
                "name": "Cliente Seed",
                "email": "cliente.seed@example.com",
                "phone": "11999990000",
                "address": "Rua Seed, 100",
                "is_active": True,
            },
        )
        return customer

    def _seed_products(self):
        base_products = [
            {
                "sku": "SEED-NB-001",
                "name": "Notebook Seed",
                "description": "Notebook para ambiente de desenvolvimento",
                "price": Decimal("4500.00"),
                "stock_quantity": 20,
                "is_active": True,
            },
            {
                "sku": "SEED-MS-001",
                "name": "Mouse Seed",
                "description": "Mouse para ambiente de desenvolvimento",
                "price": Decimal("150.00"),
                "stock_quantity": 50,
                "is_active": True,
            },
        ]

        products = {}
        for product_data in base_products:
            product, _ = Product.objects.update_or_create(
                sku=product_data["sku"],
                defaults=product_data,
            )
            products[product.sku] = product

        return products

    def _seed_order(self, customer, products):
        notebook = products["SEED-NB-001"]
        mouse = products["SEED-MS-001"]

        order_total = notebook.price + (mouse.price * 2)
        order, _ = Order.objects.update_or_create(
            idempotency_key="seed-order-001",
            defaults={
                "customer": customer,
                "status": OrderStatus.CONFIRMED,
                "observations": "Pedido de seed para desenvolvimento",
                "total_amount": order_total,
            },
        )

        self._upsert_order_item(order, notebook, quantity=1)
        self._upsert_order_item(order, mouse, quantity=2)

        OrderStatusHistory.objects.update_or_create(
            order=order,
            previous_status=OrderStatus.PENDING,
            new_status=OrderStatus.CONFIRMED,
            defaults={
                "changed_by": "seed-command",
                "reason": "Confirmação automática no seed inicial",
            },
        )

    def _upsert_order_item(self, order, product, quantity):
        unit_price = product.price
        subtotal = unit_price * quantity
        OrderItem.objects.update_or_create(
            order=order,
            product=product,
            defaults={
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            },
        )
