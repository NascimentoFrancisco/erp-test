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


@pytest.mark.django_db
def test_filter_products_by_sku(api_client):
    product_1 = Product.objects.create(
        sku="SKU-AAA",
        name="Notebook Pro",
        description="Descrição A",
        price=1000,
        stock_quantity=10,
        is_active=True,
    )
    Product.objects.create(
        sku="SKU-BBB",
        name="Mouse Gamer",
        description="Descrição B",
        price=200,
        stock_quantity=15,
        is_active=True,
    )

    response = api_client.get(f"/api/v1/products/?sku={product_1.sku}")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(product_1.id)


@pytest.mark.django_db
def test_filter_products_by_name_exact(api_client):
    product_1 = Product.objects.create(
        sku="SKU-AAA",
        name="Notebook Pro",
        description="Descrição A",
        price=1000,
        stock_quantity=10,
        is_active=True,
    )
    Product.objects.create(
        sku="SKU-BBB",
        name="Notebook Air",
        description="Descrição B",
        price=2000,
        stock_quantity=15,
        is_active=True,
    )

    response = api_client.get("/api/v1/products/?name=Notebook Pro")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(product_1.id)


@pytest.mark.django_db
def test_filter_products_by_name_like(api_client):
    product_1 = Product.objects.create(
        sku="SKU-AAA",
        name="Notebook Pro",
        description="Descrição A",
        price=1000,
        stock_quantity=10,
        is_active=True,
    )
    Product.objects.create(
        sku="SKU-BBB",
        name="Mouse Gamer",
        description="Descrição B",
        price=200,
        stock_quantity=15,
        is_active=True,
    )

    response = api_client.get("/api/v1/products/?name_like=note")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(product_1.id)


@pytest.mark.django_db
def test_filter_products_by_is_active(api_client):
    active_product = Product.objects.create(
        sku="SKU-AAA",
        name="Produto Ativo",
        description="Descrição A",
        price=1000,
        stock_quantity=10,
        is_active=True,
    )
    Product.objects.create(
        sku="SKU-BBB",
        name="Produto Inativo",
        description="Descrição B",
        price=200,
        stock_quantity=15,
        is_active=False,
    )

    response = api_client.get("/api/v1/products/?is_active=true")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(active_product.id)
