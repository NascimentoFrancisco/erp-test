from rest_framework.test import APIClient


def test_health_endpoint_returns_ok():
    client = APIClient()

    response = client.get("/health/")

    assert response.status_code == 200
    assert response.data == {"status": "ok"}
