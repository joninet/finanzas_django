from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Sum, Count
from django.conf import settings
from django.contrib import messages
import json
import os
from datetime import datetime, timedelta
from calendar import monthrange

from .models import MedioPago, Categoria, Movimiento, Gasto, Ingreso
from .google_sheets.sheets_api import sync_gastos_to_sheets as sheets_sync_gastos
from .google_sheets.sheets_api import sync_ingresos_to_sheets as sheets_sync_ingresos
from .google_sheets.sheets_api import sync_medios_pago_to_sheets as sheets_sync_medios
from .google_sheets.sheets_api import sync_categorias_to_sheets as sheets_sync_categorias
from .google_sheets.sheets_api import import_from_sheets as sheets_import
from .google_sheets.sheets_api import CREDENTIALS_FILE

# Vistas principales

def dashboard(request):
    """Dashboard principal con resumen de finanzas personales"""
    # Obtener fecha actual y primer día del mes
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Estadísticas del mes actual
    gastos_mes = Movimiento.objects.filter(
        tipo='gasto',
        fecha__gte=primer_dia_mes,
        fecha__lte=hoy
    )
    
    ingresos_mes = Movimiento.objects.filter(
        tipo='ingreso',
        fecha__gte=primer_dia_mes,
        fecha__lte=hoy
    )
    
    # Totales
    total_gastos = gastos_mes.aggregate(total=Sum('monto'))['total'] or 0
    total_ingresos = ingresos_mes.aggregate(total=Sum('monto'))['total'] or 0
    balance = total_ingresos - total_gastos
    
    # Gastos por categoría
    gastos_por_categoria = gastos_mes.values('categoria').annotate(
        total=Sum('monto')
    ).order_by('-total')
    
    # Próximos gastos mensuales pendientes
    gastos_pendientes = Movimiento.objects.filter(
        tipo='gasto',
        estado='pendiente',
        fecha__gte=hoy
    ).order_by('fecha')[:5]
    
    contexto = {
        'titulo': 'Dashboard',
        'total_gastos': total_gastos,
        'total_ingresos': total_ingresos,
        'balance': balance,
        'gastos_por_categoria': gastos_por_categoria,
        'gastos_pendientes': gastos_pendientes,
        'mes_actual': hoy.strftime('%B %Y')
    }
    
    return render(request, 'core/dashboard.html', contexto)


def gastos_diarios(request):
    """Vista para gestionar gastos diarios"""
    # Obtener medios de pago activos
    medios_pago = MedioPago.objects.filter(activo=True).order_by('nombre')
    
    # Obtener categorías de gastos
    categorias = Categoria.objects.filter(tipo='gasto', activo=True).order_by('nombre')
    
    # Obtener gastos diarios (del último mes)
    fecha_limite = timezone.now().date() - timedelta(days=30)
    gastos_diarios = Gasto.objects.filter(
        categoria='variable',
        fecha__gte=fecha_limite
    ).order_by('-fecha')
    
    contexto = {
        'titulo': 'Gastos Diarios',
        'medios_pago': medios_pago,
        'categorias': categorias,
        'gastos_diarios': gastos_diarios,
    }
    
    return render(request, 'core/gastos_diarios.html', contexto)


def gastos_mensuales(request):
    """Vista para gestionar gastos mensuales"""
    # Obtener medios de pago activos
    medios_pago = MedioPago.objects.filter(activo=True).order_by('nombre')
    
    # Obtener categorías de gastos
    categorias = Categoria.objects.filter(tipo='gasto', activo=True).order_by('nombre')
    
    # Generar lista de los últimos 12 meses
    hoy = timezone.now().date()
    meses = []
    
    for i in range(12):
        fecha = hoy - timedelta(days=30*i)
        mes_anio = fecha.strftime("%m-%Y")
        nombre_mes = fecha.strftime("%B %Y")
        meses.append({'valor': mes_anio, 'nombre': nombre_mes})
    
    # Obtener gastos mensuales
    gastos_mensuales = Gasto.objects.filter(
        categoria='fijo',
    ).order_by('-fecha')
    
    # Obtener mes actual
    mes_actual = hoy.strftime("%m-%Y")
    
    contexto = {
        'titulo': 'Gastos Mensuales',
        'medios_pago': medios_pago,
        'categorias': categorias,
        'gastos_mensuales': gastos_mensuales,
        'meses': meses,
        'mes_actual': mes_actual
    }
    
    return render(request, 'core/gastos_mensuales.html', contexto)


def ingresos(request):
    """Vista para gestionar ingresos"""
    # Obtener medios de pago activos
    medios_pago = MedioPago.objects.filter(activo=True).order_by('nombre')
    
    # Obtener categorías de ingresos
    categorias = Categoria.objects.filter(tipo='ingreso', activo=True).order_by('nombre')
    
    # Obtener ingresos (del último año)
    fecha_limite = timezone.now().date() - timedelta(days=365)
    lista_ingresos = Ingreso.objects.filter(
        fecha__gte=fecha_limite
    ).order_by('-fecha')
    
    contexto = {
        'titulo': 'Ingresos',
        'medios_pago': medios_pago,
        'categorias': categorias,
        'ingresos': lista_ingresos,
    }
    
    return render(request, 'core/ingresos.html', contexto)


# API views para operaciones CRUD

@require_POST
def crear_gasto(request):
    """Crea un nuevo gasto"""
    try:
        # Obtener datos del formulario
        concepto = request.POST.get('concepto')
        monto = request.POST.get('monto')
        fecha = request.POST.get('fecha')
        categoria = request.POST.get('categoria', 'variable')  # variable o fijo
        medio_pago_id = request.POST.get('medio_pago')
        observaciones = request.POST.get('observaciones', '')
        
        # Validar datos básicos
        if not all([concepto, monto, fecha, medio_pago_id]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        # Convertir fecha
        try:
            try:
                # Intentar primero con formato ISO (YYYY-MM-DD) del input type="date"
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                # Si falla, intentar con formato dd/mm/yyyy
                fecha_obj = datetime.strptime(fecha, '%d/%m/%Y').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido. Use YYYY-MM-DD o DD/MM/YYYY'}, status=400)
        
        # Obtener medio de pago
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id)
        
        # Crear gasto
        gasto = Gasto.objects.create(
            concepto=concepto,
            monto=monto,
            fecha=fecha_obj,
            categoria=categoria,
            medio_pago=medio_pago,
            observaciones=observaciones
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Gasto creado exitosamente',
            'id': gasto.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_gasto(request, gasto_id):
    """Elimina un gasto existente"""
    try:
        gasto = get_object_or_404(Gasto, id=gasto_id)
        gasto.delete()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Gasto eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def cambiar_estado_gasto(request, gasto_id):
    """Cambia el estado de un gasto"""
    try:
        gasto = get_object_or_404(Gasto, id=gasto_id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado not in ['pendiente', 'cancelado', 'pagado']:
            return JsonResponse({'error': 'Estado inválido'}, status=400)
        
        gasto.estado = nuevo_estado
        gasto.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Estado cambiado a {nuevo_estado}',
            'id': gasto.id,
            'estado': gasto.estado
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def crear_ingreso(request):
    """Crea un nuevo ingreso"""
    try:
        # Obtener datos del formulario
        concepto = request.POST.get('concepto')
        monto = request.POST.get('monto')
        fecha = request.POST.get('fecha')
        categoria = request.POST.get('categoria', 'variable')  # variable o fijo
        medio_pago_id = request.POST.get('medio_pago')
        observaciones = request.POST.get('observaciones', '')
        
        # Validar datos básicos
        if not all([concepto, monto, fecha, medio_pago_id]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        # Convertir fecha
        try:
            try:
                # Intentar primero con formato ISO (YYYY-MM-DD) del input type="date"
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                # Si falla, intentar con formato dd/mm/yyyy
                fecha_obj = datetime.strptime(fecha, '%d/%m/%Y').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido. Use YYYY-MM-DD o DD/MM/YYYY'}, status=400)
        
        # Obtener medio de pago
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id)
        
        # Crear ingreso
        ingreso = Ingreso.objects.create(
            concepto=concepto,
            monto=monto,
            fecha=fecha_obj,
            categoria=categoria,
            medio_pago=medio_pago,
            observaciones=observaciones
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Ingreso registrado exitosamente',
            'id': ingreso.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_ingreso(request, ingreso_id):
    """Elimina un ingreso existente"""
    try:
        ingreso = get_object_or_404(Ingreso, id=ingreso_id)
        ingreso.delete()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Ingreso eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def listar_medios_pago(request):
    """Retorna la lista de medios de pago disponibles"""
    try:
        medios_pago = MedioPago.objects.filter(activo=True).values('id', 'nombre')
        return JsonResponse(list(medios_pago), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def crear_medio_pago(request):
    """Crea un nuevo medio de pago"""
    try:
        nombre = request.POST.get('nombre')
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido'}, status=400)
        
        # Verificar si ya existe
        if MedioPago.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un medio de pago con ese nombre'}, status=400)
            
        medio_pago = MedioPago.objects.create(nombre=nombre)
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Medio de pago creado exitosamente',
            'id': medio_pago.id,
            'nombre': medio_pago.nombre
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_medio_pago(request, medio_id):
    """Elimina un medio de pago existente"""
    try:
        medio_pago = get_object_or_404(MedioPago, id=medio_id)
        
        # Verificar si tiene movimientos asociados
        if Movimiento.objects.filter(medio_pago=medio_pago).exists():
            # No eliminamos el medio de pago, solo lo desactivamos
            medio_pago.activo = False
            medio_pago.save()
            mensaje = 'Medio de pago desactivado (tenía movimientos asociados)'
        else:
            # Si no tiene movimientos, lo eliminamos
            medio_pago.delete()
            mensaje = 'Medio de pago eliminado exitosamente'
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def medios_pago(request):
    """Vista para gestionar medios de pago"""
    # Obtener medios de pago activos
    medios_pago = MedioPago.objects.filter(activo=True).order_by('nombre')
    
    contexto = {
        'titulo': 'Medios de Pago',
        'medios_pago': medios_pago,
    }
    
    return render(request, 'core/medios_pago.html', contexto)


def categorias(request):
    """Vista para gestionar categorías"""
    # Obtener categorías activas, separadas por tipo
    categorias_gastos = Categoria.objects.filter(tipo='gasto', activo=True).order_by('nombre')
    categorias_ingresos = Categoria.objects.filter(tipo='ingreso', activo=True).order_by('nombre')
    
    contexto = {
        'titulo': 'Categorías',
        'categorias_gastos': categorias_gastos,
        'categorias_ingresos': categorias_ingresos,
    }
    
    return render(request, 'core/categorias.html', contexto)


@require_POST
def crear_categoria(request):
    """Crea una nueva categoría"""
    try:
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')  # gasto o ingreso
        icono = request.POST.get('icono')
        color = request.POST.get('color')
        
        # Validaciones básicas
        if not all([nombre, tipo, icono, color]):
            return JsonResponse({'error': 'Todos los campos son requeridos'}, status=400)
            
        if tipo not in ['gasto', 'ingreso']:
            return JsonResponse({'error': 'Tipo inválido'}, status=400)
        
        # Verificar si ya existe
        if Categoria.objects.filter(nombre=nombre, tipo=tipo).exists():
            return JsonResponse({'error': 'Ya existe una categoría con ese nombre y tipo'}, status=400)
            
        categoria = Categoria.objects.create(
            nombre=nombre,
            tipo=tipo,
            icono=icono,
            color=color
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Categoría creada exitosamente',
            'id': categoria.id,
            'nombre': categoria.nombre
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_categoria(request, categoria_id):
    """Elimina una categoría existente"""
    try:
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        # Verificar si tiene movimientos asociados
        if Movimiento.objects.filter(categoria=categoria).exists():
            # No eliminamos la categoría, solo la desactivamos
            categoria.activo = False
            categoria.save()
            mensaje = 'Categoría desactivada (tenía movimientos asociados)'
        else:
            # Si no tiene movimientos, la eliminamos
            categoria.delete()
            mensaje = 'Categoría eliminada exitosamente'
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Vistas y API para Google Sheets

def sincronizacion_sheets(request):
    """Vista para la página de sincronización con Google Sheets"""
    # Verificar si existen las credenciales
    credenciales_existen = os.path.exists(CREDENTIALS_FILE)
    
    contexto = {
        'titulo': 'Sincronización con Google Sheets',
        'credenciales_existen': credenciales_existen,
        'gastos_sheet_id': getattr(settings, 'GASTOS_SHEET_ID', ''),
        'ingresos_sheet_id': getattr(settings, 'INGRESOS_SHEET_ID', '')
    }
    
    return render(request, 'core/sincronizacion_sheets_fix.html', contexto)


@require_POST
def sync_gastos_to_sheets(request):
    """Sincroniza los gastos a Google Sheets"""
    try:
        from django.contrib import messages
        from django.shortcuts import redirect
        
        resultado = sheets_sync_gastos()
        
        if 'error' in resultado:
            messages.error(request, f"Error: {resultado['error']}")
        else:
            messages.success(request, resultado.get('message', 'Gastos sincronizados exitosamente'))
        
        return redirect('core:sincronizacion_sheets')
    
    except Exception as e:
        from django.contrib import messages
        from django.shortcuts import redirect
        
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:sincronizacion_sheets')


@require_POST
def sync_ingresos_to_sheets(request):
    """Sincroniza los ingresos a Google Sheets"""
    try:
        resultado = sheets_sync_ingresos()
        
        if 'error' in resultado:
            messages.error(request, f"Error: {resultado['error']}")
        else:
            messages.success(request, resultado.get('message', 'Ingresos sincronizados exitosamente'))
        
        return redirect('core:sincronizacion_sheets')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:sincronizacion_sheets')


@require_POST
def sync_medios_pago_to_sheets(request):
    """Sincroniza los medios de pago a Google Sheets"""
    try:
        resultado = sheets_sync_medios()
        
        if 'error' in resultado:
            messages.error(request, f"Error: {resultado['error']}")
        else:
            messages.success(request, resultado.get('message', 'Medios de pago sincronizados exitosamente'))
        
        return redirect('core:sincronizacion_sheets')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:sincronizacion_sheets')


@require_POST
def sync_categorias_to_sheets(request):
    """Sincroniza las categorías a Google Sheets"""
    try:
        resultado = sheets_sync_categorias()
        
        if 'error' in resultado:
            messages.error(request, f"Error: {resultado['error']}")
        else:
            messages.success(request, resultado.get('message', 'Categorías sincronizadas exitosamente'))
        
        return redirect('core:sincronizacion_sheets')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:sincronizacion_sheets')


@require_POST
def import_from_sheets(request):
    """Importa datos desde Google Sheets"""
    try:
        resultados = sheets_import()
        
        # Verificar si hay errores en alguno de los resultados
        errores = []
        for tipo, resultado in resultados.items():
            if 'error' in resultado:
                errores.append(f"{tipo}: {resultado['error']}")
        
        if errores:
            messages.error(request, f"Errores: {', '.join(errores)}")
            return redirect('core:sincronizacion_sheets')
        
        # Construir mensaje de éxito
        mensajes = []
        for tipo, resultado in resultados.items():
            if 'message' in resultado:
                mensajes.append(resultado['message'])
        
        messages.success(request, ' | '.join(mensajes))
        return redirect('core:sincronizacion_sheets')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:sincronizacion_sheets')
