from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User, CustomerProfile


class UserCreationFormCustom(forms.ModelForm):
    """Formulario personalizado para crear usuarios con email como USERNAME_FIELD."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'rut', 'phone')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords don\'t match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Información de Despacho Opcional (Cliente)'
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationFormCustom
    
    inlines = (CustomerProfileInline, )
    
    list_display = ('id', 'email', 'first_name', 'last_name', 'rut', 'phone', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'rut')
    ordering = ('email',)
    
    add_fieldsets = (
        (None, {'fields': ('email', 'username')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'rut', 'phone')}),
        ('Password', {'fields': ('password1', 'password2')}),
    )
    
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
