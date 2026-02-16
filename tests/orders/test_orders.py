import uuid
import threading
import pytest
from rest_framework.test import APIClient
from apps.customers.models import Customer
from apps.products.models import Product
from apps.orders.models import Order, OrderItem, OrderStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer():
    return Customer.objects.create(
        name="Cliente Pedido",
        document="52998224725",
        email="cliente@pedido.com",
        phone="11999999999",
        address="Rua Pedido",
        is_active=True,
    )


@pytest.fixture
def product():
    return Product.objects.create(
        sku="GZ-TR",
        name="Produto Teste",
        price=100,
        stock_quantity=10,
        is_active=True,
    )


@pytest.fixture
def product_no_stock():
    return Product.objects.create(
        sku="GF-TK",
        name="Produto Sem Estoque",
        price=50,
        stock_quantity=0,
        is_active=True,
    )


@pytest.mark.django_db
def test_create_order_success(api_client, customer, product):
    payload = {
        "customer_id": str(customer.id),
        "idempotency_key": "key-123",
        "items": [
            {
                "product_id": str(product.id),
                "quantity": 2
            }
        ]
    }

    response = api_client.post("/api/v1/orders/", payload, format="json")

    assert response.status_code == 201
    assert Order.objects.count() == 1

    product.refresh_from_db()
    assert product.stock_quantity == 8


@pytest.mark.django_db
def test_order_fails_without_stock(api_client, customer, product, product_no_stock):
    payload = {
        "customer_id": str(customer.id),
        "idempotency_key": "key-fail",
        "items": [
            {"product_id": str(product.id), "quantity": 2},
            {"product_id": str(product_no_stock.id), "quantity": 1},
        ]
    }

    response = api_client.post("/api/v1/orders/", payload, format="json")

    assert response.status_code == 400
    assert Order.objects.count() == 0

    product.refresh_from_db()
    assert product.stock_quantity == 10


@pytest.mark.django_db
def test_order_idempotency(api_client, customer, product):
    payload = {
        "customer_id": str(customer.id),
        "idempotency_key": "same-key",
        "items": [
            {"product_id": str(product.id), "quantity": 1}
        ]
    }

    r1 = api_client.post("/api/v1/orders/", payload, format="json")
    r2 = api_client.post("/api/v1/orders/", payload, format="json")
    r3 = api_client.post("/api/v1/orders/", payload, format="json")

    assert Order.objects.count() == 1
    assert r1.data["id"] == r2.data["id"] == r3.data["id"]


@pytest.mark.django_db(transaction=True)
def test_stock_concurrency(customer, product):

    product.stock_quantity = 10
    product.save()

    payload = {
        "customer_id": str(customer.id),
        "idempotency_key": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(product.id),
                "quantity": 8
            }
        ]
    }

    responses = []

    def make_request():
        client = APIClient()
        response = client.post("/api/v1/orders/", payload, format="json")
        responses.append(response.status_code)

    t1 = threading.Thread(target=make_request)
    t2 = threading.Thread(target=make_request)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    product.refresh_from_db()

    assert responses.count(201) == 1
    assert responses.count(400) == 1
    assert product.stock_quantity in [2, 10]


@pytest.mark.django_db
def test_valid_status_transition(api_client, customer, product):
    order = Order.objects.create(
        customer=customer,
        total_amount=100,
        idempotency_key="status-key"
    )

    response = api_client.patch(
        f"/api/v1/orders/{order.id}/status/",
        {"new_status": OrderStatus.CONFIRMED},
        format="json"
    )

    assert response.status_code == 200

    order.refresh_from_db()
    assert order.status == OrderStatus.CONFIRMED


@pytest.mark.django_db
def test_invalid_status_transition(api_client, customer):
    order = Order.objects.create(
        customer=customer,
        total_amount=100,
        idempotency_key="invalid-status"
    )

    response = api_client.patch(
        f"/api/v1/orders/{order.id}/status/",
        {"new_status": OrderStatus.SHIPPED},
        format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_cancel_order_returns_stock(api_client, customer, product):

    order = Order.objects.create(
        customer=customer,
        total_amount=0,
        idempotency_key="cancel-key"
    )

    product.stock_quantity = 10
    product.save()

    product.stock_quantity -= 2
    product.save()

    from apps.orders.models import OrderItem
    OrderItem.objects.create(
        id=uuid.uuid4(),
        order=order,
        product=product,
        quantity=2,
        unit_price=100,
        subtotal=200,
    )

    response = api_client.delete(f"/api/v1/orders/{order.id}/")

    assert response.status_code == 204

    product.refresh_from_db()
    assert product.stock_quantity == 10


@pytest.mark.django_db
def test_create_order_with_inactive_customer(api_client, customer, product):
    customer.is_active = False
    customer.save()

    payload = {
        "customer_id": str(customer.id),
        "idempotency_key": "inactive-key",
        "items": [
            {"product_id": str(product.id), "quantity": 1}
        ]
    }

    response = api_client.post("/api/v1/orders/", payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_list_order_items(api_client, customer, product):
    order = Order.objects.create(
        customer=customer,
        total_amount=200,
        idempotency_key="items-key"
    )

    item = OrderItem.objects.create(
        id=uuid.uuid4(),
        order=order,
        product=product,
        quantity=2,
        unit_price=100,
        subtotal=200,
    )

    response = api_client.get(f"/api/v1/orders/{order.id}/items/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == str(item.id)
    assert response.data[0]["product"] == product.id
    assert response.data[0]["product_name"] == product.name
    assert response.data[0]["quantity"] == 2


@pytest.mark.django_db
def test_list_order_items_returns_404_when_order_does_not_exist(api_client):
    response = api_client.get(f"/api/v1/orders/{uuid.uuid4()}/items/")

    assert response.status_code == 404
