import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    try:
        cache.clear()
    except Exception:
        pass
