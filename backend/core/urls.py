from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from apps.products.views import ProductViewSet, SupplierViewSet, CategoryViewSet, StockMovementViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from apps.authentication.views import CustomTokenObtainPairView, CustomTokenRefreshView, RegisterView, UserMeView

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, 'products')
router.register(r'suppliers', SupplierViewSet, 'suppliers')
router.register(r'categories', CategoryViewSet, 'categories')
router.register(r'stock-movements', StockMovementViewSet, 'stock_movements')

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/me/', UserMeView.as_view(), name='auth_me'),
    # Swagger / OpenAPI schema endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc')
]
