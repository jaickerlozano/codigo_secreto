from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .images import normalize_uploaded_image


class ProductImageNormalizationMixin:
    """Normalize only newly assigned product images before their first storage save."""

    image_normalization_field = "image"

    def clean(self):
        super().clean()
        self._normalize_pending_image()

    def save(self, *args, **kwargs):
        self._normalize_pending_image()
        return super().save(*args, **kwargs)

    def _normalize_pending_image(self):
        image = getattr(self, self.image_normalization_field)
        if (
            not image
            or image._committed
            or getattr(image, "_product_image_normalized", False)
            or getattr(getattr(image, "file", None), "_product_image_normalized", False)
        ):
            return

        try:
            normalized = normalize_uploaded_image(image)
        except ValidationError as error:
            raise ValidationError({self.image_normalization_field: error.messages}) from error

        setattr(self, self.image_normalization_field, normalized)
        getattr(self, self.image_normalization_field)._product_image_normalized = True

# Create your models here.

class Product(ProductImageNormalizationMixin, models.Model):
    name = models.CharField(max_length=255, verbose_name='nombre')
    description = models.TextField(null=True, blank=True, verbose_name='descripción')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products', verbose_name='categoría')
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='products', verbose_name='proveedor')
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    price = models.IntegerField(db_index=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='imagen')

    # Campos SKU y UI para catálogo e integración frontend
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name='SKU')
    icon = models.CharField(max_length=100, default='box', verbose_name='icono')
    gradient = models.CharField(max_length=200, default='from-gray-500 to-gray-700', verbose_name='gradiente')
    experience_level = models.PositiveSmallIntegerField(
        default=3,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='nivel de experiencia',
        db_index=True
    )
    features = models.JSONField(default=list, verbose_name='características')
    badge = models.CharField(max_length=50, null=True, blank=True, verbose_name='badge')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de actualización')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Productos'
        verbose_name = 'Producto'


class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name='nombre')
    contact = models.CharField(max_length=255, verbose_name='contacto')
    email = models.EmailField(verbose_name='correo electrónico')
    phone = models.CharField(max_length=20, verbose_name='teléfono')
    address = models.TextField(verbose_name='dirección')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Proveedores'
        verbose_name = 'Proveedor'

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='nombre')
    description = models.TextField(null=True, blank=True, verbose_name='descripción')

    # Este campo será para crear la jerarquía de categorías. Si es null, es una categoría raíz. Si tiene valor, es una subcategoría de la categoría indicada.
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories', verbose_name='categoría padre', db_index=True)

    def __str__(self):
        category_name = self.name or "Categoría sin nombre"
        
        # Evaluamos si tiene padre de forma plana (sin recursión)
        if self.parent_id and self.parent:
            # self.parent.name obtiene el string del padre directamente, evitando bucles infinitos
            parent_name = self.parent.name or "Categoría Padre"
            return f"{parent_name} > {category_name}"
            
        return category_name

    class Meta:
        verbose_name_plural = 'Categorías'
        verbose_name = 'Categoría'

class StockMovement(models.Model):
    TYPES = (('IN', 'Entrada'), ('OUT', 'Salida'))
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='stock_movements', verbose_name='producto')
    description = models.TextField(null=True, blank=True, verbose_name='descripción')
    movement_type = models.CharField(max_length=3, choices=TYPES, verbose_name='tipo de movimiento')
    quantity = models.PositiveIntegerField(verbose_name='cantidad')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='fecha y hora')

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"

    def clean(self):
        super().clean()
        
        # Validamos solo si es un registro nuevo y están todos los datos necesarios
        if not self.pk and self.product_id and self.movement_type == 'OUT' and self.quantity:
            # Consultamos el stock actual de forma plana para la validación del formulario
            if self.quantity > self.product.current_stock:
                raise ValidationError({
                    "quantity": f"Stock insuficiente. Stock actual disponible: {self.product.current_stock}."
                })

    def save(self, *args, **kwargs):
        # Si el registro ya existe, bloqueamos su edición (regla de oro histórica)
        if self.pk:
            return

        self.full_clean()

        with transaction.atomic():
            # 1. Bloqueo la fila del producto INMEDIATAMENTE antes de leer su stock actual
            product = Product.objects.select_for_update().get(id=self.product_id)

            # 2. Ejecuto la validación de negocio con el stock real y fresco de la base de datos
            if self.movement_type == 'OUT':
                held = InventoryReservationLine.objects.filter(
                    product_id=product.id,
                    reservation__status="ACTIVE",
                    reservation__expires_at__gt=timezone.now(),
                ).aggregate(total=models.Sum("quantity"))["total"] or 0
                if self.quantity > product.current_stock - held:
                    raise ValidationError({"quantity": "Insufficient available stock."})
                # Restamos directamente en memoria (es seguro gracias a select_for_update)
                product.current_stock -= self.quantity
            else:
                # Sumamos directamente en memoria
                product.current_stock += self.quantity

            # 3. Guardamos primero el movimiento (ahora que sabemos que es válido)
            product.save()

            # 4. Guardamos el movimiento de stock en la base de datos de forma nativa
            super().save(*args, **kwargs)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Movimientos de Stock'
        verbose_name = 'Movimiento de Stock' 


class InventoryReservation(models.Model):
    STATUS_CHOICES = (("ACTIVE", "Active"), ("RELEASED", "Released"), ("COMMITTED", "Committed"))
    RELEASE_REASONS = (("EXPIRED", "Expired"), ("CANCELLED", "Cancelled"))
    order_id = models.PositiveBigIntegerField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    expires_at = models.DateTimeField()
    transitioned_at = models.DateTimeField(null=True, blank=True)
    release_reason = models.CharField(max_length=10, choices=RELEASE_REASONS, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "expires_at"], name="products_res_status_expiry")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "RELEASED", "COMMITTED"]) & (
                    models.Q(status="ACTIVE", transitioned_at__isnull=True, release_reason__isnull=True)
                    | models.Q(status="RELEASED", transitioned_at__isnull=False, release_reason__isnull=False, release_reason__in=["EXPIRED", "CANCELLED"])
                    | models.Q(status="COMMITTED", transitioned_at__isnull=False, release_reason__isnull=True)
                ),
                name="products_reservation_terminal_metadata",
            )
        ]


class InventoryReservationLine(models.Model):
    reservation = models.ForeignKey(InventoryReservation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="reservation_lines")
    quantity = models.PositiveIntegerField()
    stock_movement = models.OneToOneField(
        StockMovement, on_delete=models.PROTECT, related_name="reservation_line", null=True, blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="products_reservation_line_positive_quantity"),
            models.UniqueConstraint(fields=("reservation", "product"), name="products_reservation_line_product_unique"),
        ]


class ProductImage(ProductImageNormalizationMixin, models.Model):
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='images', # Importante: permitirá acceder a la galería desde el producto
        verbose_name='producto'
    )
    # Al igual que el modelo principal, el MediaCloudinaryStorage se encargará de subir esto a Cloudinary
    image = models.ImageField(
        upload_to='products/gallery/', 
        verbose_name='imagen de galería'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='fecha de creación'
    )

    def __str__(self):
        return f"Galería {self.id} - {self.product.name}"

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Imagen de Galería'
        verbose_name_plural = 'Imágenes de Galería'


class Favorite(models.Model):
    """Favorito privado de un cliente autenticado."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites', verbose_name='usuario')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorites', verbose_name='producto')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')

    def __str__(self):
        return f"{self.user.email} → {self.product.name}"

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_user_product_favorite')]
        ordering = ['-created_at']
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
