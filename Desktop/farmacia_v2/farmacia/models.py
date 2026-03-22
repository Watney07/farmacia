"""
MODELOS — Sistema de Farmacia Grupo 6
======================================
Los datos se exponen a través de Serializers como JSON para la API.

Relaciones:
  Lote     → ForeignKey → Medicamento
  Venta    → ForeignKey → Medicamento
  Venta    → ForeignKey → Lote
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class Medicamento(models.Model):
    """
    Catálogo de medicamentos de la farmacia.
    Cada medicamento puede tener varios Lotes (entradas de inventario).
    """
    nombre           = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion      = models.TextField(blank=True, verbose_name='Descripción')
    precio_unitario  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    requiere_receta  = models.BooleanField(default=False, verbose_name='Requiere receta')
    activo           = models.BooleanField(default=True, verbose_name='Activo')
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering            = ['nombre']

    def __str__(self):
        return self.nombre

    def stock_total(self):
        """Suma las unidades disponibles de todos los lotes no vencidos."""
        hoy = timezone.now().date()
        return sum(
            lote.cantidad_disponible
            for lote in self.lotes.filter(fecha_vencimiento__gte=hoy, cantidad_disponible__gt=0)
        )

    def tiene_stock_bajo(self):
        """Retorna True si el stock total es menor a 10 unidades."""
        return self.stock_total() < 10

    def lotes_por_vencer(self):
        """Retorna lotes que vencen en menos de 30 días."""
        hoy   = timezone.now().date()
        limite = hoy + timedelta(days=30)
        return self.lotes.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=limite,
            cantidad_disponible__gt=0
        )


class Lote(models.Model):
    """
    Entrada de inventario de un medicamento.
    La regla FIFO usa el lote con fecha_vencimiento más próxima primero.
    """
    medicamento       = models.ForeignKey(
                            Medicamento,
                            on_delete=models.CASCADE,
                            related_name='lotes',
                            verbose_name='Medicamento')
    numero_lote       = models.CharField(max_length=100, unique=True, verbose_name='Número de lote')
    fecha_vencimiento = models.DateField(verbose_name='Fecha de vencimiento')
    cantidad_inicial  = models.PositiveIntegerField(verbose_name='Cantidad inicial')
    cantidad_disponible = models.PositiveIntegerField(verbose_name='Cantidad disponible')
    fecha_ingreso     = models.DateField(auto_now_add=True)
    proveedor         = models.CharField(max_length=200, blank=True, verbose_name='Proveedor')

    class Meta:
        verbose_name        = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering            = ['fecha_vencimiento']   # FIFO: más próximo a vencer primero

        
    def save(self, *args, **kwargs):
        # CAMBIO: asegurar que SIEMPRE se persista el modelo. 
        # Antes solo guardaba cuando cantidad_disponible era None, lo que impedía crear/actualizar lotes.
        if self.cantidad_disponible is None:
            self.cantidad_disponible = self.cantidad_inicial
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Lote {self.numero_lote} — {self.medicamento.nombre} (vence: {self.fecha_vencimiento})'

    def esta_vencido(self):
        return self.fecha_vencimiento < timezone.now().date()

    def dias_para_vencer(self):
        return (self.fecha_vencimiento - timezone.now().date()).days

    def por_vencer(self):
        """True si vence en menos de 30 días y no está vencido."""
        return 0 <= self.dias_para_vencer() <= 30


class Venta(models.Model):
    """
    Registro de cada venta.
    Al crear una Venta, el serializer descuenta automáticamente
    del lote más antiguo disponible (lógica FIFO).
    """
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('cancelada',  'Cancelada'),
    ]

    medicamento          = models.ForeignKey(
                               Medicamento,
                               on_delete=models.PROTECT,
                               related_name='ventas',
                               verbose_name='Medicamento')
    lote_usado           = models.ForeignKey(
                               Lote,
                               on_delete=models.PROTECT,
                               related_name='ventas',
                               null=True, blank=True,
                               verbose_name='Lote usado')
    cantidad             = models.PositiveIntegerField(verbose_name='Cantidad')
    precio_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    total                = models.DecimalField(max_digits=12, decimal_places=2,
                                               editable=False, default=0, verbose_name='Total')
    cliente_nombre       = models.CharField(max_length=200, blank=True, verbose_name='Cliente')
    estado               = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada')
    fecha_venta          = models.DateTimeField(auto_now_add=True)
    observaciones        = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering            = ['-fecha_venta']

    def __str__(self):
        return f'Venta #{self.id} — {self.medicamento.nombre} x{self.cantidad}'

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario_venta
        super().save(*args, **kwargs)
