import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0008_favorite"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryReservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.PositiveBigIntegerField(unique=True)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("RELEASED", "Released"), ("COMMITTED", "Committed")], max_length=10)),
                ("expires_at", models.DateTimeField()),
                ("transitioned_at", models.DateTimeField(blank=True, null=True)),
                ("release_reason", models.CharField(blank=True, choices=[("EXPIRED", "Expired"), ("CANCELLED", "Cancelled")], max_length=10, null=True)),
            ],
            options={
                "indexes": [models.Index(fields=["status", "expires_at"], name="products_res_status_expiry")],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(status__in=["ACTIVE", "RELEASED", "COMMITTED"]) & (
                            models.Q(status="ACTIVE", transitioned_at__isnull=True, release_reason__isnull=True)
                            | models.Q(status="RELEASED", transitioned_at__isnull=False, release_reason__isnull=False, release_reason__in=["EXPIRED", "CANCELLED"])
                            | models.Q(status="COMMITTED", transitioned_at__isnull=False, release_reason__isnull=True)
                        ),
                        name="products_reservation_terminal_metadata",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="InventoryReservationLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reservation_lines", to="products.product")),
                ("reservation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="products.inventoryreservation")),
                ("stock_movement", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reservation_line", to="products.stockmovement")),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(condition=models.Q(quantity__gt=0), name="products_reservation_line_positive_quantity"),
                    models.UniqueConstraint(fields=("reservation", "product"), name="products_reservation_line_product_unique"),
                ],
            },
        ),
    ]
