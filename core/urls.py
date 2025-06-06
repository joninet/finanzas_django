from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Vistas principales
    path('', views.dashboard, name='dashboard'),
    path('gastos-diarios/', views.gastos_diarios, name='gastos_diarios'),
    path('gastos-mensuales/', views.gastos_mensuales, name='gastos_mensuales'),
    path('ingresos/', views.ingresos, name='ingresos'),
    path('medios-pago/', views.medios_pago, name='medios_pago'),
    path('categorias/', views.categorias, name='categorias'),
    
    # API para gastos e ingresos
    path('api/gasto/crear/', views.crear_gasto, name='crear_gasto'),
    path('api/gasto/<int:gasto_id>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    path('api/gasto/<int:gasto_id>/cambiar-estado/', views.cambiar_estado_gasto, name='cambiar_estado_gasto'),
    path('api/ingreso/crear/', views.crear_ingreso, name='crear_ingreso'),
    path('api/ingreso/<int:ingreso_id>/eliminar/', views.eliminar_ingreso, name='eliminar_ingreso'),
    
    # API para medios de pago
    path('api/medio-pago/listar/', views.listar_medios_pago, name='listar_medios_pago'),
    path('api/medio-pago/crear/', views.crear_medio_pago, name='crear_medio_pago'),
    path('api/medio-pago/<int:medio_id>/eliminar/', views.eliminar_medio_pago, name='eliminar_medio_pago'),
    
    # API para categorías
    path('api/categoria/crear/', views.crear_categoria, name='crear_categoria'),
    path('api/categoria/<int:categoria_id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # API para sincronización con Google Sheets
    path('api/sheets/sync-gastos/', views.sync_gastos_to_sheets, name='sync_gastos_sheets'),
    path('api/sheets/sync-ingresos/', views.sync_ingresos_to_sheets, name='sync_ingresos_sheets'),
    path('api/sheets/sync-medios-pago/', views.sync_medios_pago_to_sheets, name='sync_medios_pago_sheets'),
    path('api/sheets/sync-categorias/', views.sync_categorias_to_sheets, name='sync_categorias_sheets'),
    path('api/sheets/import/', views.import_from_sheets, name='import_sheets'),
    path('sync-sheets/', views.sincronizacion_sheets, name='sincronizacion_sheets'),
]
