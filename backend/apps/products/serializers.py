from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement
from django.core.exceptions import ValidationError as DjangoValidationError

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
    # Campo dinámico que llamará recursivamente a este mismo serializador para traer a las hijas
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'subcategories']

    def get_subcategories(self, obj):   
        # Si la categoría tiene subcategorías, las serializamos usando este mismo molde
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []
    


class StockMovementSerializer(serializers.ModelSerializer):
    alert = serializers.CharField(read_only=True) # Necesario para agregar el campo temporal
    
    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'movement_type', 'quantity', 'timestamp', 'alert']

    # Captura el error del modelo y lo traduce a formato API (JSON)
    def create(self, validated_data):
        try:
            # Llama al save() inteligente del modelo que ya programamos
            return super().create(validated_data)
        except DjangoValidationError as e:
            # Traduce el error nativo de Django a un ValidationError de Django REST Framework
            raise serializers.ValidationError(e.message_dict)