from django.db import models
from apps.products.models import Product
from apps.authentication.models import User

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name='usuario')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de actualización')

    def __str__(self):
        return f"Carro de {self.user.email}"

    class Meta:
        verbose_name = 'Carro de Compras'
        verbose_name_plural = 'Carros de Compras'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='carro')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items', verbose_name='producto')
    quantity = models.PositiveIntegerField(default=1, verbose_name='cantidad')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Carro: {self.cart.user.email})"
    
    # NUEVO MÉTODO ÚTIL: Calcula el subtotal en pesos chilenos directamente desde el modelo
    @property
    def subtotal(self):
        return self.quantity * self.product.price
    
    class Meta:
        verbose_name = 'Ítem del Carro'
        verbose_name_plural = 'Ítems de los Carros'
        unique_together = ('cart', 'product')
