from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    # Para evitar que el cliente intente manipular el stock directamente, lo dejamos como read-only. El stock se maneja a través de movimientos de stock.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            
        # Si la instancia ya existe, estamos actualizando (PUT/PATCH)
        if self.instance is not None:
            self.fields['current_stock'].read_only = True


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