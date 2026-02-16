import random
import uuid

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.customers.models import Customer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer():
    return Customer.objects.create(
        name="Cliente Teste",
        document="12345678901",
        email="cliente@teste.com",
        phone="11999999999",
        address="Rua Teste",
    )


@pytest.mark.django_db
def test_list_customers(api_client, customer):
    response = api_client.get("/api/v1/customers/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_create_customer(api_client):
    data = {
        "name": "Novo Cliente",
        "document": "98765432100",
        "email": "novo@teste.com",
        "phone": "11888888888",
        "address": "Rua Nova",
    }

    response = api_client.post("/api/v1/customers/", data)

    assert response.status_code == 201
    assert Customer.objects.count() == 1


@pytest.mark.django_db
def test_soft_delete_customer(api_client, customer):
    response = api_client.delete(f"/api/v1/customers/{customer.id}/")

    assert response.status_code == 204
    assert Customer.objects.count() == 0
    assert Customer.all_objects.count() == 1
    assert Customer.all_objects.first().deleted_at is not None


@pytest.mark.django_db
def test_create_customer_invalid_document(api_client):
    data = {
        "name": "Cliente Inválido",
        "document": "123",
        "email": "invalido@teste.com",
        "phone": "11999999999",
        "address": "Rua Teste",
    }

    response = api_client.post("/api/v1/customers/", data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "document" in response.data


@pytest.mark.django_db
def test_create_customer_duplicate_document(api_client, customer):
    data = {
        "name": "Outro Cliente",
        "document": customer.document,
        "email": "outro@teste.com",
        "phone": "11999999999",
        "address": "Rua Teste",
    }

    response = api_client.post("/api/v1/customers/", data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_customer_duplicate_email(api_client, customer):
    data = {
        "name": "Outro Cliente",
        "document": "52998224725",  # CPF válido
        "email": customer.email,
        "phone": "11999999999",
        "address": "Rua Teste",
    }

    response = api_client.post("/api/v1/customers/", data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["name", "document", "email", "phone", "address"])
def test_required_fields(api_client, field):
    data = {
        "name": "Cliente",
        "document": "52998224725",
        "email": f"{uuid.uuid4()}@teste.com",
        "phone": "11999999999",
        "address": "Rua Teste",
    }

    data.pop(field)

    response = api_client.post("/api/v1/customers/", data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_ordering_by_created_at(api_client):
    c1 = Customer.objects.create(
        name="Cliente 1",
        document="52998224725",
        email="1@teste.com",
        phone="111",
        address="Rua 1",
    )

    c2 = Customer.objects.create(
        name="Cliente 2",
        document="16899535009",
        email="2@teste.com",
        phone="222",
        address="Rua 2",
    )

    response = api_client.get("/api/v1/customers/")

    results = response.data["results"]

    assert results[0]["id"] == str(c2.id)
    assert results[1]["id"] == str(c1.id)


@pytest.mark.django_db
def test_soft_deleted_customer_not_listed(api_client, customer):
    customer.delete()

    response = api_client.get("/api/v1/customers/")

    assert response.status_code == 200
    assert response.data["total"] == 0


VALID_CPFS = [
    "52998224725",
    "16899535009",
    "11144477735",
    "93541134780",
    "39053344705",
]


def generate_valid_cpf():
    return random.choice(VALID_CPFS)


@pytest.mark.django_db
def test_bulk_create_100_customers(api_client):
    for i in range(100):

        cache.clear()

        data = {
            "name": f"Cliente {i}",
            "document": generate_valid_cpf(),
            "email": f"cliente{i}@teste.com",
            "phone": f"1199999{i}",
            "address": "Rua Teste",
        }

        response = api_client.post("/api/v1/customers/", data)

        assert response.status_code in [201, 400]

    assert Customer.objects.count() >= len(VALID_CPFS)


@pytest.mark.django_db
def test_filter_customers_by_document(api_client):
    customer_1 = Customer.objects.create(
        name="Cliente 1",
        document="52998224725",
        email="cliente1@teste.com",
        phone="111111111",
        address="Rua 1",
        is_active=True,
    )
    Customer.objects.create(
        name="Cliente 2",
        document="16899535009",
        email="cliente2@teste.com",
        phone="222222222",
        address="Rua 2",
        is_active=True,
    )

    response = api_client.get(f"/api/v1/customers/?document={customer_1.document}")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(customer_1.id)


@pytest.mark.django_db
def test_filter_customers_by_email(api_client):
    customer_1 = Customer.objects.create(
        name="Cliente 1",
        document="52998224725",
        email="cliente1@teste.com",
        phone="111111111",
        address="Rua 1",
        is_active=True,
    )
    Customer.objects.create(
        name="Cliente 2",
        document="16899535009",
        email="cliente2@teste.com",
        phone="222222222",
        address="Rua 2",
        is_active=True,
    )

    response = api_client.get(f"/api/v1/customers/?email={customer_1.email}")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(customer_1.id)


@pytest.mark.django_db
def test_filter_customers_by_is_active(api_client):
    active_customer = Customer.objects.create(
        name="Cliente Ativo",
        document="52998224725",
        email="ativo@teste.com",
        phone="111111111",
        address="Rua 1",
        is_active=True,
    )
    Customer.objects.create(
        name="Cliente Inativo",
        document="16899535009",
        email="inativo@teste.com",
        phone="222222222",
        address="Rua 2",
        is_active=False,
    )

    response = api_client.get("/api/v1/customers/?is_active=true")

    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["results"][0]["id"] == str(active_customer.id)
