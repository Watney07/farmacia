"""
SERIALIZERS — Sistema de Farmacia Grupo 6
==========================================
Un Serializer convierte objetos Python (instancias de modelos) ↔ JSON.

Analogía: es como forms.py pero para JSON en vez de HTML.

Dirección de conversión:
  Modelo Python  →  Serializer  →  JSON  (cuando el cliente pide datos: GET)
  JSON           →  Serializer  →  Modelo Python  (cuando el cliente envía datos: POST/PUT)
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Medicamento, Lote, Venta


# ══════════════════════════════════════════════════════════════════
# MEDICAMENTO
# ══════════════════════════════════════════════════════════════════

class MedicamentoSerializer(serializers.ModelSerializer):
    """
    Serializer de Medicamento.
    Incluye campos calculados: stock_total, stock_bajo, lotes_por_vencer_count.
    """
    # SerializerMethodField → campo calculado, no viene del modelo directamente
    stock_total           = serializers.SerializerMethodField()
    stock_bajo            = serializers.SerializerMethodField()
    lotes_por_vencer_count = serializers.SerializerMethodField()
    # CAMBIO: usado para mostrar una fecha de vencimiento en la tabla de medicamentos
    proximo_vencimiento   = serializers.SerializerMethodField()

    class Meta:
        model  = Medicamento
        fields = [
            'id', 'nombre', 'descripcion', 'precio_unitario',
            'requiere_receta', 'activo', 'creado_en',
            'stock_total', 'stock_bajo', 'lotes_por_vencer_count',
            'proximo_vencimiento'
        ]
        read_only_fields = ['id', 'creado_en']

    def get_stock_total(self, obj):
        return obj.stock_total()

    def get_stock_bajo(self, obj):
        return obj.tiene_stock_bajo()

    def get_lotes_por_vencer_count(self, obj):
        return obj.lotes_por_vencer().count()

    def get_proximo_vencimiento(self, obj):
        """
        CAMBIO: próximo vencimiento (fecha más cercana) entre lotes no vencidos con stock.
        Se usa para que el frontend pueda mostrar la fecha en la tabla de medicamentos.
        """
        hoy = timezone.now().date()
        lote = obj.lotes.filter(
            fecha_vencimiento__gte=hoy,
            cantidad_disponible__gt=0,
        ).order_by('fecha_vencimiento').only('fecha_vencimiento').first()
        return lote.fecha_vencimiento if lote else None

    def validate_precio_unitario(self, value):
        """
        validate_<campo>() → validación personalizada por campo.
        Equivalente a clean_<campo>() en formularios Django.
        """
        if value <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a $0.")
        return value

    def validate_nombre(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre del medicamento debe tener al menos 3 caracteres."
            )
        return value.strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Al crear, la descripción es obligatoria.
        if self.instance is None:
            descripcion = attrs.get('descripcion', '')
            if not isinstance(descripcion, str) or not descripcion.strip():
                raise serializers.ValidationError(
                    {"descripcion": "La descripción es obligatoria."}
                )
            attrs['descripcion'] = descripcion.strip()
        else:
            # En edición, si llega el campo, lo normalizamos y no permitimos vacío.
            if 'descripcion' in attrs:
                descripcion = attrs.get('descripcion', '')
                if not isinstance(descripcion, str) or not descripcion.strip():
                    raise serializers.ValidationError(
                        {"descripcion": "La descripción no puede estar vacía."}
                    )
                attrs['descripcion'] = descripcion.strip()

        return attrs


# ══════════════════════════════════════════════════════════════════
# LOTE
# ══════════════════════════════════════════════════════════════════

class LoteSerializer(serializers.ModelSerializer):
    """
    Serializer de Lote con campos calculados de vencimiento.
    source='medicamento.nombre' → accede al atributo del objeto relacionado.
    """
    medicamento_nombre = serializers.CharField(source='medicamento.nombre', read_only=True)
    esta_vencido       = serializers.SerializerMethodField()
    dias_para_vencer   = serializers.SerializerMethodField()
    alerta_vencimiento = serializers.SerializerMethodField()

    class Meta:
        model  = Lote
        fields = [
            'id', 'medicamento', 'medicamento_nombre', 'numero_lote',
            'fecha_vencimiento', 'cantidad_inicial', 'cantidad_disponible',
            'fecha_ingreso', 'proveedor',
            'esta_vencido', 'dias_para_vencer', 'alerta_vencimiento'
        ]
        # CAMBIO: permitir editar `cantidad_disponible` (stock actual) desde la API.
        # id y la fecha de ingreso queda como solo lectura
        read_only_fields = ['id', 'fecha_ingreso']

    def get_esta_vencido(self, obj):
        return obj.esta_vencido()

    def get_dias_para_vencer(self, obj):
        return obj.dias_para_vencer()

    def get_alerta_vencimiento(self, obj):
        return obj.por_vencer()

    def create(self, validated_data):
        # Al crear un lote, cantidad_disponible = cantidad_inicial
        validated_data['cantidad_disponible'] = validated_data['cantidad_inicial']
        return super().create(validated_data)

    def validate_fecha_vencimiento(self, value):
        """La fecha de vencimiento debe ser futura."""
        if value <= timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de vencimiento debe ser una fecha futura."
            )
        return value

    def validate_cantidad_inicial(self, value):
        if value < 1:
            raise serializers.ValidationError("La cantidad inicial debe ser al menos 1 unidad.")
        return value

    def validate_cantidad_disponible(self, value):
        # CAMBIO: validación explícita para edición de stock actual.
        if value < 0:
            raise serializers.ValidationError("La cantidad disponible no puede ser negativa.")
        return value

    def validate_numero_lote(self, value):
        if not value.strip():
            raise serializers.ValidationError("El número de lote no puede estar vacío.")
        return value.strip().upper()


# ══════════════════════════════════════════════════════════════════
# VENTA
# ══════════════════════════════════════════════════════════════════

class VentaSerializer(serializers.ModelSerializer):
    """
    Serializer de Venta.
    Al crear (POST), ejecuta la lógica FIFO automáticamente:
    usa el lote más antiguo disponible y descuenta el inventario.
    """
    medicamento_nombre = serializers.CharField(source='medicamento.nombre', read_only=True)
    lote_numero        = serializers.CharField(source='lote_usado.numero_lote', read_only=True)
    alerta_stock_bajo  = serializers.SerializerMethodField()

    class Meta:
        model  = Venta
        fields = [
            'id', 'medicamento', 'medicamento_nombre',
            'lote_usado', 'lote_numero',
            'cantidad', 'precio_unitario_venta', 'total',
            'cliente_nombre', 'estado', 'fecha_venta',
            'observaciones', 'alerta_stock_bajo'
        ]
        read_only_fields = ['id', 'total', 'lote_usado', 'precio_unitario_venta', 'fecha_venta']

    def get_alerta_stock_bajo(self, obj):
        return obj.medicamento.tiene_stock_bajo()

    def validate_cantidad(self, value):
        if value < 1:
            raise serializers.ValidationError("La cantidad debe ser al menos 1 unidad.")
        return value

    def validate(self, data):
        """
        validate() (sin nombre de campo) → validación cruzada.
        Se ejecuta DESPUÉS de todas las validate_<campo>().

        ⚙ REGLA DE NEGOCIO — FIFO:
        Verifica stock disponible usando solo lotes no vencidos,
        ordenados por fecha_vencimiento (más antiguo primero).
        """
        medicamento = data.get('medicamento')
        cantidad    = data.get('cantidad', 0)

        if medicamento:
            hoy = timezone.now().date()
            # FIFO: lotes ordenados por fecha_vencimiento (más próximo a vencer primero)
            lotes_disponibles = medicamento.lotes.filter(
                fecha_vencimiento__gte=hoy,
                cantidad_disponible__gt=0
            ).order_by('fecha_vencimiento')

            stock_disponible = sum(l.cantidad_disponible for l in lotes_disponibles)

            if stock_disponible == 0:
                raise serializers.ValidationError(
                    f"No hay stock disponible de '{medicamento.nombre}'."
                )
            if cantidad > stock_disponible:
                raise serializers.ValidationError(
                    f"Stock insuficiente. Disponible: {stock_disponible} unidades."
                )

            # Guardar el lote FIFO para usarlo en create()
            self._lote_fifo = lotes_disponibles.first()

        return data

    def create(self, validated_data):
        medicamento = validated_data['medicamento']
        cantidad    = validated_data['cantidad']
    
        from django.utils import timezone
        hoy = timezone.now().date()
        lote = medicamento.lotes.filter(
            fecha_vencimiento__gte=hoy,
            cantidad_disponible__gt=0
        ).order_by('fecha_vencimiento').first()

        print(f">>> LOTE: {lote} | ANTES: {lote.cantidad_disponible} | CANT: {cantidad}")

        validated_data['precio_unitario_venta'] = medicamento.precio_unitario
        validated_data['lote_usado']            = lote

    
        from django.db.models import F
        medicamento.lotes.filter(pk=lote.pk).update(
                cantidad_disponible=F('cantidad_disponible') - cantidad
    )

        print(f">>> DESPUES: {lote.cantidad_disponible}")

        venta = Venta(**validated_data)
        venta.save()
        return venta

# ══════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════

class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos usuarios.
    password2 → campo adicional para confirmar contraseña.
    write_only=True → el campo se acepta al crear pero NO aparece en la respuesta GET.
    """
    password  = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con ese correo.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate(self, data):
        """
        validate() → validación cruzada de múltiples campos.
        Se ejecuta DESPUÉS de todas las validate_<campo>().
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        # create_user() hashea la contraseña correctamente
        return User.objects.create_user(**validated_data)
