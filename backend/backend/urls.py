from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("equipment_api.urls")),
    path("api/auth/", include("rest_framework.urls")),
]




