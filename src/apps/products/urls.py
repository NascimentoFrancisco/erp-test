from django.urls import path

from apps.products.views import ProductViewSet

urlpatterns = [
    path("", ProductViewSet.as_view({"get": "list", "post": "create"})),
    path("<uuid:id>/", ProductViewSet.as_view({"get": "retrieve", "patch": "partial_update"})),
    path("<uuid:id>/stock/", ProductViewSet.as_view({"patch": "update_stock"})),
]
