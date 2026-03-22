"""
URLs PRINCIPALES — API REST Farmacia Grupo 6
=============================================
Usamos DefaultRouter de DRF para generar automáticamente
las URLs de los ViewSets.

El router genera estas rutas automáticamente:
  GET    /api/medicamentos/             → lista
  POST   /api/medicamentos/             → crear
  GET    /api/medicamentos/{id}/        → detalle
  PUT    /api/medicamentos/{id}/        → reemplazar
  PATCH  /api/medicamentos/{id}/        → actualizar parcialmente
  DELETE /api/medicamentos/{id}/        → eliminar
  GET    /api/medicamentos/alertas/     → regla de negocio especial

Igual para lotes y ventas.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from farmacia import views

# ── Router DRF ────────────────────────────────────────────────────────────────
router = DefaultRouter()
router.register(r'medicamentos', views.MedicamentoViewSet, basename='medicamento')
router.register(r'lotes',        views.LoteViewSet,        basename='lote')
router.register(r'ventas',       views.VentaViewSet,       basename='venta')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Todas las URLs de la API viven bajo /api/
    path('api/', include(router.urls)),

    # Endpoints de autenticación:
    # POST /api/auth/registro/  → crear cuenta
    # POST /api/auth/login/     → obtener token
    # POST /api/auth/logout/    → invalidar token
    # GET  /api/auth/perfil/    → datos del usuario actual
    path('api/auth/', include('farmacia.auth_urls')),

    # Interfaz navegable de DRF (solo en DEBUG=True)
    path('api-auth/', include('rest_framework.urls')),

    # Frontend (templates Django)
    path('', include('farmacia.frontend_urls')),
]
