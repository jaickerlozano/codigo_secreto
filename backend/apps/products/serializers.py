from rest_framework import serializers
from .models import Product, Supplier, Category, StockMovement, ProductImage, Favorite
from django.core.exceptions import ValidationError as DjangoValidationError
from .images import (
    delivery_width_for_serializer_context,
    product_image_original_url,
    product_image_url,
)

#   NUEVO SERIALIZADOR: Formatea de forma individual las fotos secundarias de la galería
class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    image_original = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_original']

    def get_image(self, obj) -> str | None:
        return product_image_url(
            obj.image,
            max_width=delivery_width_for_serializer_context(self.context),
        )

    def get_image_original(self, obj) -> str | None:
        return product_image_original_url(
            obj.image,
            max_width=delivery_width_for_serializer_context(self.context),
        )


class CategoryNameField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if not hasattr(value, 'name'):
            value = Category.objects.get(pk=value.pk)
        return value.name


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    image_original = serializers.SerializerMethodField()
    
    # CONEXIÓN CON EL ARRAY: Anidamos la galería usando el relacionado 'images' del modelo.
    # Marcamos many=True porque es una lista, y read_only=True para proteger la integridad.
    images = ProductImageSerializer(many=True, read_only=True)

    category = CategoryNameField(queryset=Category.objects.all())
    stock = serializers.IntegerField(source='current_stock', read_only=True)
    experience_level = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        # ADICIÓN: Incluimos 'images' explícitamente en el listado de campos para React
        fields = [
            'id', 'name', 'sku', 'price', 'description', 'image', 'image_original',
            'images',  # <--- Inyectamos el array aquí
            'gradient', 'icon', 'badge', 'features', 
            'category', 'stock', 'experience_level',
            'current_stock', 'minimum_stock', 'supplier', 'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['current_stock'].read_only = True

    def get_image(self, obj) -> str | None:
        return product_image_url(
            obj.image,
            max_width=delivery_width_for_serializer_context(self.context),
        )

    def get_image_original(self, obj) -> str | None:
        return product_image_original_url(
            obj.image,
            max_width=delivery_width_for_serializer_context(self.context),
        )

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


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = fields


class FavoriteMergeSerializer(serializers.Serializer):
    product_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)
