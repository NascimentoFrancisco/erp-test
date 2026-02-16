import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.django_db
@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-rate-limit",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.AllowAny",
        ],
        "DEFAULT_THROTTLE_CLASSES": [
            "apps.core.throttles.ClientOrIPRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "client": "2/hour",
        },
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_PAGINATION_CLASS": "apps.core.paginator.PersonalPagination",
    },
)
def test_rate_limit_blocks_after_limit_per_hour():
    cache.clear()
    client = APIClient()

    first_response = client.get("/api/v1/orders/")
    second_response = client.get("/api/v1/orders/")
    blocked_response = client.get("/api/v1/orders/")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert blocked_response.status_code == 429
