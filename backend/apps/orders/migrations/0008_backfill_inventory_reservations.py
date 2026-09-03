from collections import defaultdict
from datetime import timedelta

from django.db import migrations
from django.utils import timezone


HOLD_DURATION = timedelta(minutes=15)


def backfill_inventory_reservations(apps, schema_editor):
    """Create historical reservation rows while checkout writes are quiesced."""
    Order = apps.get_model("orders", "Order")
    OrderItem = apps.get_model("orders", "OrderItem")
    Product = apps.get_model("products", "Product")
    Reservation = apps.get_model("products", "InventoryReservation")
    ReservationLine = apps.get_model("products", "InventoryReservationLine")
    database = schema_editor.connection.alias
    now = timezone.now()
    allocated = defaultdict(int)
    products = {}
    plans = []

    for order in Order.objects.using(database).filter(status="PENDING").order_by("created_at", "pk"):
        expires_at = order.created_at + HOLD_DURATION
        active = expires_at > now
        lines = []
        items = OrderItem.objects.using(database).filter(order_id=order.pk).order_by("product_id", "pk")
        for item in items:
            if item.product_id is None:
                raise RuntimeError(f"Legacy pending order {order.pk} has a missing product.")
            if item.quantity <= 0:
                raise RuntimeError(f"Legacy pending order {order.pk} has a non-positive quantity.")
            product = products.get(item.product_id)
            if product is None:
                product = Product.objects.using(database).filter(pk=item.product_id).first()
                if product is None:
                    raise RuntimeError(f"Legacy pending order {order.pk} has a missing product.")
                products[item.product_id] = product
            if active:
                allocated[item.product_id] += item.quantity
                if allocated[item.product_id] > product.current_stock:
                    raise RuntimeError(f"Legacy active allocation for product {product.pk} exceeds physical stock.")
            lines.append((item.product_id, item.quantity))
        if not lines:
            raise RuntimeError(f"Legacy pending order {order.pk} has no product allocation.")
        plans.append((order.pk, expires_at, active, lines))

    for order_id, expires_at, active, lines in plans:
        reservation = Reservation.objects.using(database).create(
            order_id=order_id,
            status="ACTIVE" if active else "RELEASED",
            expires_at=expires_at,
            transitioned_at=None if active else now,
            release_reason=None if active else "EXPIRED",
        )
        ReservationLine.objects.using(database).bulk_create(
            [ReservationLine(reservation_id=reservation.pk, product_id=product_id, quantity=quantity) for product_id, quantity in lines]
        )
        if not active:
            Order.objects.using(database).filter(pk=order_id).update(status="CANCELLED", updated_at=now)


class Migration(migrations.Migration):
    atomic = True
    dependencies = [
        ("orders", "0007_notificationdelivery_due_index"),
        ("products", "0009_inventory_reservations"),
    ]

    operations = [
        # Reversal is schema-only; historical order status is never rewritten.
        migrations.RunPython(backfill_inventory_reservations, migrations.RunPython.noop),
    ]
