from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0013_order_cancellation_reason')]
    operations = [
        migrations.AlterField(
            model_name='notificationdelivery', name='event',
            field=models.CharField(max_length=30, verbose_name='evento', choices=[
                ('payment_confirmation', 'Confirmación de Pago'), ('dispatch', 'Despacho del Pedido'),
                ('delivered', 'Entrega del Pedido'), ('cancelled', 'Cancelación del Pedido'),
                ('pending_payment_receipt', 'Pedido Pendiente de Pago'),
            ]),
        ),
        migrations.AlterField(
            model_name='notificationdelivery', name='status',
            field=models.CharField(max_length=10, default='PENDING', verbose_name='estado', choices=[
                ('PENDING', 'Pendiente'), ('SENT', 'Enviado'), ('FAILED', 'Fallido'), ('SKIPPED', 'Omitido'),
            ]),
        ),
    ]
