from django.db import models
from apps.orders.models import Order

class Transaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente de Pago'),
        ('APPROVED', 'Aprobado / Exitoso'),
        ('REJECTED', 'Rechazado / Fallido'),
    )

    # Enlazamos el intento de pago a un pedido específico
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions', verbose_name='pedido')
    
    # Monto total que se mandó a cobrar (congelado en pesos chilenos)
    amount = models.PositiveIntegerField(verbose_name='monto de la transacción')
    
    # Control de estados de la pasarela
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', verbose_name='estado de transacción')
    
    # Campo clave: Guarda el token, ID o código único que nos devuelva Flow/Webpay
    gateway_reference = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID de referencia de la pasarela')
    
    # Guardamos el método utilizado si la pasarela nos lo informa (Ej: "Webpay_Débito", "Webpay_Crédito", "OneClick")
    payment_method = models.CharField(max_length=50, null=True, blank=True, verbose_name='método de pago')

    # Idempotencia: la misma clave por pedido permite reintentos sin duplicar intentos
    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='clave de idempotencia',
        help_text='Clave única por pedido que hace idempotentes los reintentos de pago.',
    )

    # Proveedor de pago que gestiona el intento (p. ej. "mock" en desarrollo)
    provider = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='proveedor de pago',
        help_text='Identificador del proveedor de pago que gestiona el intento.',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de intento')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de respuesta')

    def __str__(self):
        return f"Transacción #{self.id} - Pedido #{self.order.id} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transacción de Pago'
        verbose_name_plural = 'Transacciones de Pagos'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'idempotency_key'],
                name='unique_transaction_order_idempotency_key',
            ),
        ]
