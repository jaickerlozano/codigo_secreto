from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CustomerProfile

class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Información de Despacho Opcional (Cliente)'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (CustomerProfileInline, )
    
    list_display = ('id', 'email', 'first_name', 'last_name', 'rut', 'phone', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'rut')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'rut', 'phone')}),
        ('Permisos y Roles', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    # CORRECCIÓN: Cambiamos 'comuna' por 'province' y 'birthday' por 'birth_date'
    list_display = ('id', 'user_email', 'region', 'province', 'address', 'birth_date')
    
    # CORRECCIÓN: Cambiamos 'comuna' por 'province' para que coincida con el campo de tu modelo
    list_filter = ('region', 'province')
    search_fields = ('user__email', 'address')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Correo del Cliente"
