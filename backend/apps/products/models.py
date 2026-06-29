from django.db import models, transaction
from django.core.exceptions import ValidationError 

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='nombre')
    description = models.TextField(null=True, blank=True, verbose_name='descripción')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products', verbose_name='categoría')
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='products', verbose_name='proveedor')
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    price = models.IntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='imagen')
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
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories', verbose_name='categoría padre')

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