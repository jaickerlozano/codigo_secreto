from django.db import models

# Create your models here.
class Region(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='nombre')
    # Guardo el orden geográfico oficial de Chile (de norte a sur)
    ordinal_number = models.IntegerField(help_text='Orden geográfico de la región de Norte a Sur', verbose_name='orden geográfico')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['ordinal_number']
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'
        

class Comuna(models.Model):
    name = models.CharField(max_length=100, verbose_name='nombre')
    # Cada comuna pertenece obligatoriamente a una única región
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='comunas', verbose_name='región')

    # Campo clave para la tienda: el valor en pesos del envío a esta comuna específica
    shipping_cost = models.PositiveIntegerField(default=0, help_text='Costo de envío en CLP para esta comuna', verbose_name='costo de envío')

    # Para controlar si despachamos o no a esta zona en particular
    is_active = models.BooleanField(default=True, help_text='Indica si realizamos envíos a esta comuna')

    def __str__(self):
        return f"{self.name} ({self.region.name})"
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'
        # Evita que se repita la misma comuna dentro de la misma región
        unique_together = ('name', 'region')


    