from django.contrib import admin
from django.utils.html import format_html
from .models import Medicamento, Lote, Venta


class LoteInline(admin.TabularInline):
    model  = Lote
    extra  = 1
    fields = ['numero_lote', 'fecha_vencimiento', 'cantidad_inicial', 'cantidad_disponible', 'proveedor']
    # CAMBIO: modificar stock y vencimiento para todos los usuarios


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'precio_unitario', 'requiere_receta', 'activo', 'stock_display', 'estado_display']
    list_filter   = ['activo', 'requiere_receta']
    search_fields = ['nombre']
    inlines       = [LoteInline]

    def stock_display(self, obj):
        stock = obj.stock_total()
        color = 'red' if stock < 10 else 'green'
        return format_html('<b style="color:{}">{} uds</b>', color, stock)
    stock_display.short_description = 'Stock'

    def estado_display(self, obj):
        if obj.tiene_stock_bajo():
            return format_html('<span style="color:red">⚠ Stock bajo</span>')
        if obj.lotes_por_vencer().exists():
            return format_html('<span style="color:orange">⚠ Lotes por vencer</span>')
        return format_html('<span style="color:green">✓ OK</span>')
    estado_display.short_description = 'Estado'


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display  = ['numero_lote', 'medicamento', 'fecha_vencimiento', 'cantidad_disponible', 'estado_display']
    list_filter   = ['fecha_vencimiento']
    search_fields = ['numero_lote', 'medicamento__nombre']
    ordering      = ['fecha_vencimiento']

    def estado_display(self, obj):
        if obj.esta_vencido():
            return format_html('<span style="color:red">✗ Vencido</span>')
        if obj.por_vencer():
            return format_html('<span style="color:orange">⚠ Vence en {} días</span>', obj.dias_para_vencer())
        return format_html('<span style="color:green">✓ OK</span>')
    estado_display.short_description = 'Estado vencimiento'


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display    = ['id', 'medicamento', 'lote_usado', 'cantidad', 'total', 'cliente_nombre', 'estado', 'fecha_venta']
    list_filter     = ['estado', 'fecha_venta']
    search_fields   = ['medicamento__nombre', 'cliente_nombre']
    readonly_fields = ['total', 'lote_usado', 'precio_unitario_venta', 'fecha_venta']
    ordering        = ['-fecha_venta']
