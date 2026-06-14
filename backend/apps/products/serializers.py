from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class StockMovementSerializer(serializers.ModelSerializer):
    alert = serializers.CharField(read_only=True) # Necesario para agregar el campo temporal
    
    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'type', 'quantity', 'timestamp', 'alert']