import pytest
from rest_framework.test import APIClient
from apps.products.models import Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def product():
    return Product.objects.create(
        sku="SKU123",
        name="Produto Teste",
        description="Descrição",
        price=100.00,
        stock_quantity=10,
    )


@pytest.mark.django_db
def test_list_products(api_client, product):
    response = api_client.get("/api/v1/products/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_create_product(api_client):
    data = {
        "sku": "SKU999",
        "name": "Novo Produto",
        "description": "Desc",
        "price": 50.00,
        "stock_quantity": 5,
    }

    response = api_client.post("/api/v1/products/", data)

    assert response.status_code == 201
    assert Product.objects.count() == 1


@pytest.mark.django_db
def test_update_stock(api_client, product):
    response = api_client.patch(
        f"/api/v1/products/{product.id}/update-stock/",
        {"stock_quantity": 50}
    )

    assert response.status_code == 200

    product.refresh_from_db()
    assert product.stock_quantity == 50
