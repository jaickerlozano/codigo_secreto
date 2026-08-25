"""Process due notification deliveries in bounded batches."""
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

from apps.orders.models import NotificationDelivery
from apps.orders.notifications import attempt_delivery, STALE_PENDING_MINUTES


class Command(BaseCommand):
    help = "Process due notification deliveries."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100)

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if batch_size <= 0:
            raise CommandError("--batch-size must be positive.")
        now = timezone.now()
        stale = now - timezone.timedelta(minutes=STALE_PENDING_MINUTES)
        rows = list(
            NotificationDelivery.objects.filter(
                models.Q(status="FAILED", attempts__lt=5, next_retry_at__lte=now)
                | models.Q(status="PENDING", attempts=0, updated_at__lte=stale)
            )
            .order_by("pk")
            .values_list("pk", "attempts")[:batch_size]
        )
        ids = [pk for pk, _ in rows]
        before = dict(rows)
        totals = {"selected": len(ids), "attempted": 0, "sent": 0, "failed": 0, "exhausted": 0, "skipped": 0}
        for did in ids:
            b = before[did]
            try:
                d = attempt_delivery(did, trigger="automatic", now=now)
            except Exception as e:
                self.stderr.write(f"Unexpected error {did}: {e}")
                totals["failed"] += 1
                continue
            if d is None:
                totals["failed"] += 1
            elif d.attempts == b:
                totals["skipped"] += 1
            else:
                totals["attempted"] += 1
                totals["sent" if d.status == "SENT" else "exhausted" if d.exhausted else "failed"] += 1
        self.stdout.write(
            f"selected={totals['selected']} attempted={totals['attempted']} "
            f"sent={totals['sent']} failed={totals['failed']} "
            f"exhausted={totals['exhausted']} skipped={totals['skipped']}"
        )
