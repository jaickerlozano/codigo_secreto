from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelo de usuario personalizado para permitir campos adicionales como RUT, teléfono, etc.
# Sirve tanto para clientes como para administradores, diferenciados por el campo is_staff
class User(AbstractUser):
    email = models.EmailField(unique=True)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # Si tiene nombre y apellido cargados, los muestra de forma elegante
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.email})"
        return self.email
    
# Perfil de cliente para almacenar información adicional del usuario para aquellos que se registren como clientes
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Customer Profile for {self.user.email}"