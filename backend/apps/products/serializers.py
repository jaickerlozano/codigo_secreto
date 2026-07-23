from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement, ProductImage
from django.core.exceptions import ValidationError as DjangoValidationError

#   NUEVO SERIALIZADOR: Formatea de forma individual las fotos secundarias de la galería
class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

    def get_image(self, obj):
        if not obj.image:
            return ""
        url = obj.image.url
        # Aplicamos exactamente la misma lógica inteligente de optimización para Cloudinary
        if 'res.cloudinary.com' in url:
            if '/upload/' in url:
                url = url.replace('/upload/', '/upload/f_auto,q_auto,w_1000/')
            if not url.endswith('.webp') and not url.endswith('.png') and not url.endswith('.jpg'):
                url = f"{url}.webp"
            return url
        return url


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    # CONEXIÓN CON EL ARRAY: Anidamos la galería usando el relacionado 'images' del modelo.
    # Marcamos many=True porque es una lista, y read_only=True para proteger la integridad.
    images = ProductImageSerializer(many=True, read_only=True)

    category = serializers.CharField(source='category.name', read_only=True)
    stock = serializers.IntegerField(source='current_stock', read_only=True)
    experienceLevel = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # ADICIÓN: Incluimos 'images' explícitamente en el listado de campos para React
        fields = [
            'id', 'name', 'sku', 'price', 'description', 'image',
            'images',  # <--- Inyectamos el array aquí
            'gradient', 'icon', 'badge', 'features', 
            'category', 'stock', 'experienceLevel',
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

    def get_experienceLevel(self, obj):
        mapping = {
            1: "principiante",
            2: "intermedio",
            3: "avanzado"
        }
        return mapping.get(obj.experience_level, "principiante")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'subcategories']

    def get_subcategories(self, obj):   
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []
    

class StockMovementSerializer(serializers.ModelSerializer):
    alert = serializers.CharField(read_only=True)
    
    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'movement_type', 'quantity', 'timestamp', 'alert']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
