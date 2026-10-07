from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0011_alter_notificationdelivery_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationdelivery',
            name='event',
            field=models.CharField(
                choices=[
                    ('payment_confirmation', 'Confirmación de Pago'),
                    ('dispatch', 'Despacho del Pedido'),
                    ('delivered', 'Entrega del Pedido'),
                    ('cancelled', 'Cancelación del Pedido'),
                ],
                max_length=30,
                verbose_name='evento',
            ),
        ),
    ]
