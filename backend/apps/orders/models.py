from django.db import models
from apps.authentication.models import User
from apps.shipping.models import Comuna
from apps.products.models import Product

class Order(models.Model):
    # Estados oficiales para el flujo de un pedido
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente de Pago'),
        ('PAID', 'Pagado / Listo para Despacho'),
        ('SHIPPED', 'Enviado a Destino'),
        ('DELIVERED', 'Entregado al Cliente'),
        ('CANCELLED', 'Cancelado / Anulado'),
    )

    # 1. Datos del Comprador (Permitimos null=True para soportar "Invitados")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name='usuario')
    guest_email = models.EmailField(null=True, blank=True, verbose_name='correo invitado')
    guest_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='nombre invitado')
    phone = models.CharField(max_length=20, verbose_name='teléfono de contacto')

    # 2. Datos de Despacho en Chile
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, related_name='orders', verbose_name='comuna de entrega')
    shipping_address = models.CharField(max_length=255, verbose_name='dirección de despacho')
    apartment_office = models.CharField(max_length=50, null=True, blank=True, verbose_name='depto / oficina')

    # 3. Datos Financieros (Valores fijos en pesos chilenos)
    subtotal = models.PositiveIntegerField(verbose_name='subtotal productos')
    shipping_cost = models.PositiveIntegerField(verbose_name='costo de envío')
    total = models.PositiveIntegerField(verbose_name='total final')

    # 4. Control de Estado y Fechas
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', verbose_name='estado del pedido')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de actualización')

    def __str__(self):
        return f"Pedido #{self.id} - {self.get_status_display()} (${self.total:,})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'


class OrderItem(models.Model):
    # Relación jerárquica con la orden de compra principal
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='pedido')
    
    # Clave foránea al producto vivo (para estadísticas, pero permitimos SET_NULL por si el producto se borra del catálogo en el futuro)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items', verbose_name='producto')
    
    # REGLA DE ORO: Congelamos los datos comerciales en texto/números planos
    product_name = models.CharField(max_length=255, verbose_name='nombre del producto congelado')
    price = models.PositiveIntegerField(verbose_name='precio unitario congelado')
    quantity = models.PositiveIntegerField(verbose_name='cantidad')

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Pedido #{self.order.id})"

    @property
    def subtotal(self):
        return self.quantity * self.price

    class Meta:
        verbose_name = 'Detalle del Pedido'
        verbose_name_plural = 'Detalles de los Pedidos'
