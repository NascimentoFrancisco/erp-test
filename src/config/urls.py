from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from apps.core.views import SpectacularRapiDocView

url_v1 = "api/v1"

urlpatterns = [
    path("", SpectacularRapiDocView.as_view(url_name="schema"), name="redoc"),
    path("docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("admin/", admin.site.urls),
    path(f"{url_v1}/customers/", include("apps.customers.urls")),
    path(f"{url_v1}/products/", include("apps.products.urls")),
    path(f"{url_v1}/orders/", include("apps.orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
