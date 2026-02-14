from django.urls import path
from apps.customers.views import CustomerViewSet

urlpatterns = [
    path("", CustomerViewSet.as_view({ "get": "list", "post": "create"})),
    path("<uuid:id>/", 
        CustomerViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        )
    ),
]
