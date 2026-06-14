from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from apps.products.views import ProductViewSet, SupplierViewSet, CategoryViewSet

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, 'products')
router.register(r'suppliers', SupplierViewSet, 'suppliers')
router.register(r'categories', CategoryViewSet, 'categories')

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls))
]
