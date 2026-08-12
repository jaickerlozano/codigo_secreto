from django.db import models


class ContactMessage(models.Model):
    """Mensaje enviado por clientes desde el formulario de contacto público."""
    STATUS_NEW = 'NEW'
    STATUS_READ = 'READ'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CHOICES = (
        (STATUS_NEW, 'Nuevo'), (STATUS_READ, 'Leído'), (STATUS_RESOLVED, 'Resuelto'),
    )

    name = models.CharField(max_length=120, verbose_name='nombre')
    email = models.EmailField(verbose_name='correo electrónico')
    subject = models.CharField(max_length=200, verbose_name='asunto')
    body = models.TextField(verbose_name='mensaje')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='estado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='fecha de envío')

    def __str__(self):
        return f"{self.subject} — {self.email}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'
