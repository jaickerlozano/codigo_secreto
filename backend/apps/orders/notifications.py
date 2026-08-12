"""Durable transactional email delivery for payment confirmation and dispatch.

The row is written inside the domain transaction, the send runs on commit, a
failure never rolls back domain state, and deliveries stay retryable."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import NotificationDelivery

logger = logging.getLogger(__name__)

RETRY_DELAY_MINUTES = (15, 60, 240)  # escalating delays (minutes) by attempt count
MAX_ERROR_LENGTH = 500


def _recipient_email(order):
    return order.guest_email or (order.user.email if order.user else None)


def _subject(event, order):
    return (f"Tu pedido {order.order_number} fue despachado" if event == "dispatch"
            else f"Confirmación de pago — Pedido {order.order_number}")


def _body(event, order):
    if event == "dispatch":
        tracking = f"\nNúmero de seguimiento: {order.tracking_number}" if order.tracking_number else ""
        return (f"Hola, tu pedido {order.order_number} fue despachado con {order.carrier}.{tracking}\n"
                f"Fecha estimada de entrega: {order.estimated_delivery_date:%d/%m/%Y}.")
    total = f"${order.total:,}".replace(",", ".")
    return (f"Hola, tu pago por {total} del pedido {order.order_number} fue confirmado. Ya estamos preparando tu despacho.")


def schedule_delivery(order, event):
    """Record the durable delivery row and send it after the transaction commits."""
    delivery, _ = NotificationDelivery.objects.get_or_create(order=order, event=event)
    if delivery.status != "SENT":
        transaction.on_commit(lambda: attempt_delivery(delivery.id))
    return delivery


def attempt_delivery(delivery_id):
    """Send one delivery; a failure is recorded and never raised."""
    delivery = NotificationDelivery.objects.get(id=delivery_id)
    order = delivery.order
    if delivery.status == "SENT":
        return delivery
    delivery.attempts += 1
    try:
        recipient = _recipient_email(order)
        if not recipient:
            raise ValueError("El pedido no tiene correo de contacto.")
        send_mail(_subject(delivery.event, order), _body(delivery.event, order),
                  settings.DEFAULT_FROM_EMAIL, [recipient])
    except Exception as error:
        delivery.status = "FAILED"
        delivery.last_error = str(error)[:MAX_ERROR_LENGTH]
        delay = RETRY_DELAY_MINUTES[min(delivery.attempts - 1, len(RETRY_DELAY_MINUTES) - 1)]
        delivery.next_retry_at = timezone.now() + timezone.timedelta(minutes=delay)
        logger.warning("Notification delivery failed: order=%s event=%s error=%s", order.order_number, delivery.event, error)
    else:
        delivery.status = "SENT"
        delivery.sent_at = timezone.now()
        delivery.last_error = None
        delivery.next_retry_at = None
    delivery.save(update_fields=["status", "attempts", "last_error", "next_retry_at", "sent_at", "updated_at"])
    return delivery


def retry_delivery(delivery_id):
    """Retry one failed delivery now; other statuses are left untouched."""
    delivery = NotificationDelivery.objects.get(id=delivery_id)
    if delivery.status != "FAILED":
        return delivery
    delivery.next_retry_at = None
    delivery.save(update_fields=["next_retry_at", "updated_at"])
    return attempt_delivery(delivery.id)
