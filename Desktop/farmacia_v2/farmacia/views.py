from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from .models import Medicamento, Lote, Venta
from .serializers import (
    MedicamentoSerializer, LoteSerializer, VentaSerializer,
    RegistroSerializer,
)


# ══════════════════════════════════════════════════════════════════
# MEDICAMENTOS
# ══════════════════════════════════════════════════════════════════

class MedicamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de medicamentos.
    Cualquiera puede leer (GET); solo admins pueden crear/editar/eliminar.
    """
    serializer_class = MedicamentoSerializer

    def get_permissions(self):
        """
        get_permissions() → permite diferentes permisos según la acción.
        CAMBIO: ahora todas las acciones requieren autenticación (incluyendo list/retrieve/alertas).
        """
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        get_queryset() sobrescrito para aplicar filtros dinámicos.
        Los filtros vienen como parámetros GET en la URL:
          /api/medicamentos/?nombre=aspirina
          /api/medicamentos/?activo=true
        """
        qs = Medicamento.objects.all()
        nombre = self.request.query_params.get('nombre', '').strip()
        activo = self.request.query_params.get('activo')

        if nombre:
            qs = qs.filter(nombre__icontains=nombre)
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')
        return qs

    # CAMBIO: alertas también requiere autenticación para que, sin token,
    # el sistema no exponga información en el dashboard.
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def alertas(self, request):
        """
        @action → agrega una ruta extra al ViewSet.
        detail=False → actúa sobre la colección (no sobre un ítem específico).
        GET /api/medicamentos/alertas/

        ⚙ REGLA DE NEGOCIO ESPECIAL:
        Retorna medicamentos con stock bajo (<10 unidades)
        y lotes que vencen en menos de 30 días.
        """
        hoy    = timezone.now().date()
        limite = hoy + timedelta(days=30)

        todos       = Medicamento.objects.filter(activo=True)
        stock_bajo  = [m for m in todos if m.tiene_stock_bajo()]

        lotes_criticos = Lote.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=limite,
            cantidad_disponible__gt=0
        ).order_by('fecha_vencimiento')

        return Response({
            'stock_bajo':      MedicamentoSerializer(stock_bajo, many=True).data,
            'lotes_por_vencer': LoteSerializer(lotes_criticos, many=True).data,
            'resumen': {
                'medicamentos_stock_bajo': len(stock_bajo),
                'lotes_por_vencer':        lotes_criticos.count(),
            }
        })


# ══════════════════════════════════════════════════════════════════
# LOTES
# ══════════════════════════════════════════════════════════════════

class LoteViewSet(viewsets.ModelViewSet):
    """
    CRUD de lotes de inventario.
    La fecha_vencimiento se valida en el serializer (no puede ser pasada).
    """
    serializer_class = LoteSerializer

    def get_permissions(self):
        # CAMBIO: protegemos list/retrieve también (antes eran públicos)
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Lote.objects.select_related('medicamento').all()
        medicamento_id = self.request.query_params.get('medicamento')
        vencidos       = self.request.query_params.get('vencidos')

        if medicamento_id:
            qs = qs.filter(medicamento_id=medicamento_id)
        if vencidos == 'false':
            qs = qs.filter(fecha_vencimiento__gte=timezone.now().date())
        return qs


# ══════════════════════════════════════════════════════════════════
# VENTAS
# ══════════════════════════════════════════════════════════════════

class VentaViewSet(viewsets.ModelViewSet):
    """
    CRUD de ventas. Siempre requiere autenticación.

    Al crear (POST) se ejecuta automáticamente la lógica FIFO:
    - Se usa el lote más antiguo disponible.
    - Se descuenta el stock.
    - Si no hay stock suficiente, retorna error 400.
    """
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Venta.objects.select_related('medicamento', 'lote_usado').all()
        medicamento_id = self.request.query_params.get('medicamento')
        estado         = self.request.query_params.get('estado')

        if medicamento_id:
            qs = qs.filter(medicamento_id=medicamento_id)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/ventas/{id}/
        Cancela la venta y restaura el stock al lote original.
        """
        venta = self.get_object()
        if venta.estado == 'completada' and venta.lote_usado:
            venta.lote_usado.cantidad_disponible += venta.cantidad
            venta.lote_usado.save()
            venta.estado = 'cancelada'
            venta.save()
            return Response({'mensaje': f'Venta #{venta.id} cancelada y stock restaurado.'})
        return Response(
            {'error': 'La venta ya está cancelada.'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ══════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════

class RegistroView(generics.CreateAPIView):
    """
    POST /api/auth/registro/
    Crea un usuario y devuelve su token de autenticación.

    CreateAPIView → vista genérica que solo maneja POST para crear.
    permission_classes = [AllowAny] → cualquiera puede registrarse.
    """
    serializer_class   = RegistroSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Al registrarse, generamos y devolvemos el token directamente
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token':    token.key,
            'user_id':  user.pk,
            'username': user.username,
            'email':    user.email,
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    POST /api/auth/login/
    Body: { "username": "juan", "password": "mipassword" }
    Respuesta: { "token": "abc123...", "user_id": 1, "username": "juan" }

    El cliente guarda el token y lo envía en cada petición protegida:
      Header: Authorization: Token abc123...
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # authenticate() verifica username/password y retorna User o None
        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Credenciales incorrectas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # get_or_create → obtiene el token si ya existe, o lo crea
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token':    token.key,
            'user_id':  user.pk,
            'username': user.username,
            'email':    user.email,
            'es_admin': user.is_staff,
        })


class LogoutView(generics.GenericAPIView):
    """
    POST /api/auth/logout/
    Elimina el token del servidor → el cliente queda desautenticado.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # delete() elimina el token de la BD
        request.user.auth_token.delete()
        return Response({'mensaje': 'Sesión cerrada exitosamente.'})


class PerfilView(generics.RetrieveAPIView):
    """
    GET /api/auth/perfil/
    Devuelve los datos del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'user_id':         user.pk,
            'username':        user.username,
            'email':           user.email,
            'es_admin':        user.is_staff,
            'fecha_registro':  user.date_joined,
        })
