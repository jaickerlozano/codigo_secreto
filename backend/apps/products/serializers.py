from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement
from django.core.exceptions import ValidationError as DjangoValidationError

class ProductSerializer(serializers.ModelSerializer):
    # Sobrescribimos el campo de la imagen para personalizar su salida
    image = serializers.SerializerMethodField()

    #  SOLUCIÓN: Añadimos campos calculados de solo lectura para el frontend de React
    category = serializers.CharField(source='category.name', read_only=True)
    stock = serializers.IntegerField(source='current_stock', read_only=True)
    experienceLevel = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # En lugar de '__all__', declaramos explícitamente los campos incluyendo los nuevos en camelCase
        fields = [
            'id', 'name', 'sku', 'price', 'description', 'image',
            'gradient', 'icon', 'badge', 'features', 
            'category', 'stock', 'experienceLevel',
            # Mantenemos los originales abajo por si el administrador de Django o tus formularios internos los necesitan:
            'current_stock', 'minimum_stock', 'supplier', 'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['current_stock'].read_only = True

    def get_image(self, obj):
        if not obj.image:
            return ""
        url = obj.image.url
        if 'res.cloudinary.com' in url:
            if '/upload/' in url:
                url = url.replace('/upload/', '/upload/f_auto,q_auto,w_1000/')
            if not url.endswith('.webp') and not url.endswith('.png') and not url.endswith('.jpg'):
                url = f"{url}.webp"
            return url
        return url

    #  SOLUCIÓN: Mapea el número de experiencia (1, 2, 3) a los strings que espera tu ProductCard.tsx
    def get_experienceLevel(self, obj):
        # Si tu modelo usa un ChoiceField con texto, puedes usar: return obj.get_experience_level_display().lower()
        # Si usa enteros directos, los mapeamos explícitamente según tus estilos de CSS:
        mapping = {
            1: "principiante",
            2: "intermedio",
            3: "avanzado"
        }
        # Retorna el nivel correspondiente, o "principiante" por defecto si no coincide
        return mapping.get(obj.experience_level, "principiante")


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
            # Llama al save() inteligente del modelo que ya programé
            return super().create(validated_data)
        except DjangoValidationError as e:
            # Traduce el error nativo de Django a un ValidationError de Django REST Framework
            raise serializers.ValidationError(e.message_dict)