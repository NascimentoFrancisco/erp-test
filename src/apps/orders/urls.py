from django.urls import path
from apps.orders.views import OrderViewSet

urlpatterns = [
    path("", OrderViewSet.as_view({ "get": "list", "post": "create"})),
    path("<uuid:id>/", OrderViewSet.as_view({"get": "retrieve", "delete": "destroy"})),
    path("<uuid:id>/status/", OrderViewSet.as_view({"patch": "update_status"})),
    path("<uuid:id>/items/", OrderViewSet.as_view({"get": "items"})),
    path("<uuid:id>/status-history/", OrderViewSet.as_view({"get": "status_history"})),
]
