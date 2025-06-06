from django.contrib import admin
from .models import MedioPago, Categoria, Movimiento, Gasto, Ingreso, Configuracion

@admin.register(MedioPago)
class MedioPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'color', 'activo')
    search_fields = ('nombre',)
    list_filter = ('tipo', 'activo')

class MovimientoBaseAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'monto', 'fecha', 'categoria', 'estado', 'medio_pago')
    list_filter = ('estado', 'categoria', 'medio_pago', 'fecha')
    search_fields = ('concepto', 'observaciones')
    date_hierarchy = 'fecha'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.model, 'TIPO_VALOR'):
            return qs.filter(tipo=self.model.TIPO_VALOR)
        return qs

@admin.register(Gasto)
class GastoAdmin(MovimientoBaseAdmin):
    list_display = ('concepto', 'monto', 'fecha', 'categoria', 'estado', 'medio_pago')

@admin.register(Ingreso)
class IngresoAdmin(MovimientoBaseAdmin):
    list_display = ('concepto', 'monto', 'fecha', 'categoria', 'estado', 'medio_pago')

@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('clave', 'descripcion')
    search_fields = ('clave', 'descripcion')
