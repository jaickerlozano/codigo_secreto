"""Portable foreground expiry worker. Never activated on import or startup."""
import time

from django.core.management.base import BaseCommand, CommandError

from apps.orders.services import expire_pending_batch


class Command(BaseCommand):
    help = 'Resolve due pending orders quietly; one pass by default.'

    def add_arguments(self, parser):
        parser.add_argument('--watch', action='store_true')
        parser.add_argument('--interval', type=float, default=60)
        parser.add_argument('--batch-size', type=int, default=100)

    def handle(self, *args, **options):
        if options['interval'] <= 0 or options['batch_size'] <= 0:
            raise CommandError('interval and batch-size must be positive.')
        try:
            while True:
                count = expire_pending_batch(batch_size=options['batch_size'])
                self.stdout.write(f'Expired {count} pending order(s).')
                if not options['watch']:
                    return
                time.sleep(options['interval'])
        except KeyboardInterrupt:
            self.stdout.write('Expiry watch stopped.')
