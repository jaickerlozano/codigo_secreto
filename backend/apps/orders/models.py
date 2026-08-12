import hashlib
import hmac
import secrets
import uuid

from django.db import models
from django.utils import timezone


GUEST_ACCESS_TOKEN_BYTES = 32
GUEST_ACCESS_VALIDITY_DAYS = 90


def _guest_access_digest(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_order_number():
    """Genera un número de pedido único y legible para el cliente."""
    return f"CS-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    # Estados oficiales para el flujo de un pedido
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente de Pago'),
        ('PAID', 'Pagado / Listo para Despacho'),
        ('SHIPPED', 'Enviado a Destino'),
        ('DELIVERED', 'Entregado al Cliente'),
        ('CANCELLED', 'Cancelado / Anulado'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('webpay', 'Webpay'),
        ('flow', 'Flow'),
        ('mercadopago', 'MercadoPago'),
        ('transfer', 'Transferencia Bancaria'),
    )

    # 0. Número de pedido público (generado por el backend, nunca por el frontend)
    order_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name='número de pedido',
        help_text='Identificador público del pedido (ej: CS-XXXXXXX).',
    )

    # Clave idempotente del checkout: evita pedidos duplicados al reintentar el envío
    checkout_key = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        verbose_name='clave de checkout',
        help_text='Clave idempotente del checkout; el reintento con la misma clave devuelve el mismo pedido.',
    )

    # 1. Datos del Comprador (Permitimos null=True para soportar "Invitados")
    user = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name='usuario')
    guest_email = models.EmailField(null=True, blank=True, verbose_name='correo invitado')
    guest_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='nombre invitado')
    phone = models.CharField(max_length=20, verbose_name='teléfono de contacto')

    # 2. Datos de Despacho en Chile
    comuna = models.ForeignKey('shipping.Comuna', on_delete=models.PROTECT, related_name='orders', verbose_name='comuna de entrega')
    shipping_address = models.CharField(max_length=255, verbose_name='dirección de despacho')
    apartment_office = models.CharField(max_length=50, null=True, blank=True, verbose_name='depto / oficina')

    # 3. Método de pago seleccionado por el cliente
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='webpay',
        verbose_name='método de pago',
    )

    # 3. Datos Financieros (Valores fijos en pesos chilenos)
    subtotal = models.PositiveIntegerField(verbose_name='subtotal productos')
    shipping_cost = models.PositiveIntegerField(verbose_name='costo de envío')
    total = models.PositiveIntegerField(verbose_name='total final')

    # 4. Datos de Logística (para seguimiento del pedido)
    carrier = models.CharField(
        max_length=100,
        default='Chilexpress',
        verbose_name='transportista',
        help_text='Empresa de transporte encargada del envío.',
    )
    tracking_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='número de seguimiento',
        help_text='Código de rastreo proporcionado por el transportista.',
    )

    # 4. Tipo de entrega: estándar (fechas regulares) o especial (acuerdo previo por WhatsApp)
    DELIVERY_KIND_CHOICES = (
        ('standard', 'Entrega Estándar'),
        ('special', 'Entrega Especial'),
    )

    delivery_kind = models.CharField(
        max_length=20,
        choices=DELIVERY_KIND_CHOICES,
        default='standard',
        verbose_name='tipo de entrega',
        help_text='standard: fechas regulares de despacho; special: requiere acuerdo previo por WhatsApp.',
    )

    # Fecha especial de despacho solicitada por el cliente (solo para delivery_kind=special)
    requested_dispatch_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='fecha de despacho solicitada',
        help_text='Fecha especial de despacho solicitada por el cliente.',
    )

    # Momento en que el staff confirmó el acuerdo especial; habilita el pago
    special_delivery_agreed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='acuerdo de entrega especial',
        help_text='Momento en que el staff confirmó el acuerdo especial; sin esto el pago permanece bloqueado.',
    )

    # Registro de despacho: fecha real de despacho y fecha estimada de entrega (staff)
    dispatched_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='fecha de despacho',
        help_text='Momento en que el pedido fue despachado.',
    )
    estimated_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='fecha estimada de entrega',
        help_text='Fecha estimada de entrega registrada por el staff al despachar.',
    )

    # 4. Control de Estado y Fechas
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', verbose_name='estado del pedido')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de actualización')

    # 5. Capacidad de acceso secreto para pedidos de invitados
    guest_access_digest = models.CharField(
        max_length=64, null=True, blank=True,
        verbose_name='hash de acceso de invitado',
        help_text='SHA-256 hex digest del token de acceso. Nunca almacenar el token en claro.',
    )
    guest_access_issued_at = models.DateTimeField(null=True, blank=True, verbose_name='fecha de emisión del acceso')
    guest_access_expires_at = models.DateTimeField(null=True, blank=True, verbose_name='fecha de expiración del acceso')
    guest_access_revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='fecha de revocación del acceso')
    guest_access_version = models.PositiveIntegerField(default=0, verbose_name='versión del acceso')

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def issue_guest_access(self):
        """Generate a raw guest access token and store its SHA-256 digest."""
        raw_token = secrets.token_urlsafe(GUEST_ACCESS_TOKEN_BYTES)
        now = timezone.now()
        self.guest_access_digest = _guest_access_digest(raw_token)
        self.guest_access_issued_at = now
        self.guest_access_expires_at = now + timezone.timedelta(days=GUEST_ACCESS_VALIDITY_DAYS)
        self.guest_access_revoked_at = None
        self.guest_access_version += 1
        self.save(update_fields=[
            'guest_access_digest', 'guest_access_issued_at', 'guest_access_expires_at',
            'guest_access_revoked_at', 'guest_access_version', 'updated_at',
        ])
        return raw_token

    def verify_guest_access(self, raw_token):
        """Verify a raw token against the stored digest in constant time."""
        if not raw_token or not self.guest_access_digest:
            return False
        if self.guest_access_revoked_at is not None:
            return False
        now = timezone.now()
        if self.guest_access_issued_at and now < self.guest_access_issued_at:
            return False
        if self.guest_access_expires_at and now > self.guest_access_expires_at:
            return False
        return hmac.compare_digest(self.guest_access_digest, _guest_access_digest(raw_token))

    def revoke_guest_access(self):
        """Revoke the current guest access capability."""
        self.guest_access_revoked_at = timezone.now()
        self.save(update_fields=['guest_access_revoked_at', 'updated_at'])

    def rotate_guest_access(self):
        """Revoke the current capability and issue a new one."""
        self.revoke_guest_access()
        return self.issue_guest_access()

    def __str__(self):
        return f"Pedido #{self.id} - {self.get_status_display()} (${self.total:,})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'


class NotificationDelivery(models.Model):
    """Registro durable de cada correo transaccional (pago/despacho); el envío
    se agenda con ``transaction.on_commit`` y un fallo nunca revierte el estado."""

    EVENT_CHOICES = (
        ('payment_confirmation', 'Confirmación de Pago'),
        ('dispatch', 'Despacho del Pedido'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('FAILED', 'Fallido'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications', verbose_name='pedido')
    event = models.CharField(max_length=30, choices=EVENT_CHOICES, verbose_name='evento')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name='estado')
    attempts = models.PositiveIntegerField(default=0, verbose_name='intentos')
    last_error = models.TextField(null=True, blank=True, verbose_name='último error')
    next_retry_at = models.DateTimeField(null=True, blank=True, verbose_name='próximo reintento')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='fecha de envío')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='fecha de actualización')

    class Meta:
        unique_together = ('order', 'event')
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"{self.get_event_display()} — {self.get_status_display()} ({self.order.order_number})"


class OrderItem(models.Model):
    # Relación jerárquica con la orden de compra principal
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='pedido')
    
    # Clave foránea al producto vivo (para estadísticas, pero permitimos SET_NULL por si el producto se borra del catálogo en el futuro)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, related_name='order_items', verbose_name='producto')
    
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
