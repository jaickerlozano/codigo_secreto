from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0012_alter_notificationdelivery_event')]
    operations = [
        migrations.AddField(
            model_name='order', name='cancellation_reason',
            field=models.CharField(blank=True, default='', max_length=10,
                choices=[('BUYER', 'Comprador'), ('ADMIN', 'Administración'), ('EXPIRED', 'Plazo expirado')]),
        ),
    ]
