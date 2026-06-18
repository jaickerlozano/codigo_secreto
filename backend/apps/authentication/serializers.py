from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import User, CustomerProfile

class RegisterSerializer(serializers.ModelSerializer):
    # Definimos la contraseña con seguridad extra para que no se muestre en las respuestas GET
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'rut', 'phone', 'password', 'password_confirm')

    def validate(self, attrs):
        # 1. Validamos que ambas contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        
        # 2. Formateamos y limpiamos el RUT (Ej: "12.345.678-9" -> "123456789")
        if attrs.get('rut'):
            attrs['rut'] = attrs['rut'].replace('.', '').replace('-', '').upper().strip()
            
        return attrs

    def create(self, validated_data):
        # Eliminamos la confirmación para no intentar guardarla en el modelo
        validated_data.pop('password_confirm')
        
        with transaction.atomic():
            # El username interno de Django será igual al email para evitar conflictos
            email = validated_data['email']
            
            # Creamos el usuario utilizando el método seguro create_user (encripta la contraseña)
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                rut=validated_data.get('rut'),
                phone=validated_data.get('phone', ''),
                password=validated_data['password']
            )
            
            # Creamos automáticamente su perfil de despacho enlazado y vacío
            CustomerProfile.objects.create(user=user)
            
        return user


class UserMeSerializer(serializers.ModelSerializer):
    # Campo booleano explícito para que el frontend sepa si mostrarle o no el panel de administración
    is_admin = serializers.BooleanField(source='is_staff', read_only=True)

    class Meta:
        model = User
        # Entregamos datos limpios de identidad, excluyendo contraseñas por seguridad
        fields = ('id', 'first_name', 'last_name', 'email', 'rut', 'phone', 'is_admin')
