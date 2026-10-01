"""Durable transactional email delivery for order lifecycle events.

The row is written inside the domain transaction, the send runs on commit, a
failure never rolls back domain state, and deliveries stay retryable."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

from .models import NotificationDelivery

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = frozenset({"payment_confirmation", "dispatch", "delivered"})
RETRY_DELAY_MINUTES = (15, 60, 240, 720)
STALE_PENDING_MINUTES = 15
MAX_ERROR_LENGTH = 500


def _recipient_email(order):
    return order.guest_email or (order.user.email if order.user else None)


def _subject(event, order):
    if event == "dispatch":
        return f"Tu pedido {order.order_number} fue despachado"
    if event == "delivered":
        return f"Tu pedido {order.order_number} fue entregado"
    return f"Confirmación de pago — Pedido {order.order_number}"


def _tracking_url(order):
    url = f"{settings.ORDER_TRACKING_PUBLIC_ORIGIN}/order/{order.order_number}"
    if order.user_id is not None:
        return url

    from .services import issue_guest_email_access_ticket

    ticket = issue_guest_email_access_ticket(order)
    return f"{url}#access={ticket}" if ticket else url


def _body(event, order):
    if event == "dispatch":
        tracking = f"\nNúmero de seguimiento: {order.tracking_number}" if order.tracking_number else ""
        return (f"Hola, tu pedido {order.order_number} fue despachado con {order.carrier}.{tracking}\n"
                f"Fecha estimada de entrega: {order.estimated_delivery_date:%d/%m/%Y}.")
    if event == "delivered":
        return (f"Hola, tu pedido {order.order_number} fue entregado.\n\n"
                f"Revisa tu pedido: {_tracking_url(order)}")
    total = f"${order.total:,}".replace(",", ".")
    return (f"Hola, tu pago por {total} del pedido {order.order_number} fue confirmado. "
            f"Ya estamos preparando tu despacho.\n\nSigue tu pedido: {_tracking_url(order)}")


def _safe_delivery_error(error):
    """Keep operational diagnostics unless an exception includes the email ticket."""
    message = str(error)[:MAX_ERROR_LENGTH]
    return "Email delivery failed." if "#access=" in message else message


def schedule_delivery(order, event):
    """Record durable delivery row and, if supported, schedule initial send."""
    if event not in SUPPORTED_EVENTS:
        logger.warning("Unsupported notification event ignored: order=%s event=%s", order.order_number, event)
        return None
    delivery, _ = NotificationDelivery.objects.get_or_create(order=order, event=event)
    if delivery.status != "SENT":
        transaction.on_commit(lambda: attempt_delivery(delivery.id, trigger="initial"))
    return delivery


def attempt_delivery(delivery_id, trigger="automatic", now=None):
    """Send one delivery under row lock; failures are recorded and never raised."""
    now = now or timezone.now()
    engine = settings.DATABASES["default"]["ENGINE"]
    is_sqlite = engine.endswith("sqlite3")
    try:
        with transaction.atomic():
            delivery = NotificationDelivery.objects.select_for_update(
                skip_locked=engine.endswith("postgresql")
            ).get(id=delivery_id)
            order = delivery.order
            if is_sqlite:
                # SQLite ignores FOR UPDATE; force a write lock and re-read so
                # concurrent writers serialize before SMTP and see SENT.
                NotificationDelivery.objects.filter(pk=delivery.pk).update(attempts=models.F("attempts"))
                delivery = NotificationDelivery.objects.get(id=delivery_id)
                order = delivery.order
            if delivery.status == "SENT":
                return delivery
            eligible = False
            if trigger == "manual":
                eligible = delivery.status == "FAILED"
            elif trigger == "initial":
                eligible = delivery.status == "PENDING" and delivery.attempts == 0
            elif delivery.status == "PENDING":
                eligible = delivery.attempts == 0 and delivery.updated_at <= now - timezone.timedelta(minutes=STALE_PENDING_MINUTES)
            else:
                eligible = delivery.status == "FAILED" and delivery.attempts < 5 and delivery.next_retry_at and delivery.next_retry_at <= now
            if not eligible:
                return delivery
            delivery.attempts += 1
            try:
                recipient = _recipient_email(order)
                if not recipient:
                    raise ValueError("El pedido no tiene correo de contacto.")
                if send_mail(_subject(delivery.event, order), _body(delivery.event, order),
                             settings.DEFAULT_FROM_EMAIL, [recipient]) == 0:
                    raise RuntimeError("No recipients accepted by email backend.")
            except Exception as error:
                delivery.status = "FAILED"
                delivery.last_error = _safe_delivery_error(error)
                delivery.next_retry_at = (now + timezone.timedelta(minutes=RETRY_DELAY_MINUTES[delivery.attempts - 1])
                                           if delivery.attempts < 5 else None)
                logger.warning("Notification delivery failed: id=%s order=%s event=%s attempt=%s",
                               delivery.id, order.order_number, delivery.event, delivery.attempts)
                if delivery.exhausted:
                    logger.error("Notification delivery exhausted: id=%s order=%s event=%s attempts=%s",
                                 delivery.id, order.order_number, delivery.event, delivery.attempts)
            else:
                delivery.status, delivery.sent_at, delivery.last_error, delivery.next_retry_at = "SENT", now, None, None
            delivery.save(update_fields=["status", "attempts", "last_error", "next_retry_at", "sent_at", "updated_at"])
        return delivery
    except Exception:
        logger.exception("Unexpected error processing notification id=%s trigger=%s", delivery_id, trigger)
        return None


def retry_delivery(delivery_id):
    """Retry one failed delivery now under the same locked path."""
    return attempt_delivery(delivery_id, trigger="manual")
