from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='products')
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    # Este campo será para crear la jerarquía de categorías. Si es null, es una categoría raíz. Si tiene valor, es una subcategoría de la categoría indicada.
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        category_name = self.name or "Categoría sin nombre"
        
        # Evaluamos si tiene padre de forma plana (sin recursión)
        if self.parent_id and self.parent:
            # self.parent.name obtiene el string del padre directamente, evitando bucles infinitos
            parent_name = self.parent.name or "Categoría Padre"
            return f"{parent_name} > {category_name}"
            
        return category_name

class StockMovement(models.Model):
    TYPES = (('IN', 'Entrada'), ('OUT', 'Salida'))
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='stock_movements')
    type = models.CharField(max_length=3, choices=TYPES)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.type} - {self.quantity}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Stock Movements'
        verbose_name = 'Stock Movement' 