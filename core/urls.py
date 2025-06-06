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
    # Gasto rápido
    path('gasto-rapido/', views.gasto_rapido, name='gasto_rapido'),
    
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
    
    # Ya no usamos Google Sheets
]
