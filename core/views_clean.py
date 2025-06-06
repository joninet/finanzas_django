from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import os
from datetime import datetime, timedelta
import calendar
from decimal import Decimal

from .models import MedioPago, Categoria, Movimiento, Gasto, Ingreso

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
        total=Sum('monto'),
        nombre=Count('categoria__nombre', distinct=True)
    ).order_by('-total')
    
    # Ingresos por categoría
    ingresos_por_categoria = ingresos_mes.values('categoria').annotate(
        total=Sum('monto'),
        nombre=Count('categoria__nombre', distinct=True)
    ).order_by('-total')
    
    # Contexto para la plantilla
    context = {
        'total_gastos': total_gastos,
        'total_ingresos': total_ingresos,
        'balance': balance,
        'gastos_por_categoria': gastos_por_categoria,
        'ingresos_por_categoria': ingresos_por_categoria
    }
    
    return render(request, 'core/dashboard.html', context)


def gastos_diarios(request):
    """Vista para la página de gastos diarios"""
    # Obtener fecha actual
    hoy = timezone.now().date()
    
    # Obtener gastos del día actual
    gastos = Gasto.objects.filter(fecha=hoy).order_by('-fecha', '-id')
    
    # Calcular total
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Contexto para la plantilla
    context = {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'fecha': hoy
    }
    
    return render(request, 'core/gastos_diarios.html', context)


def gastos_mensuales(request):
    """Vista para la página de gastos mensuales"""
    # Obtener fecha actual y primer día del mes
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Obtener gastos del mes actual
    gastos = Gasto.objects.filter(
        fecha__gte=primer_dia_mes,
        fecha__lte=hoy
    ).order_by('-fecha', '-id')
    
    # Calcular total
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Contexto para la plantilla
    context = {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'mes': hoy.strftime('%B %Y')
    }
    
    return render(request, 'core/gastos_mensuales.html', context)


def ingresos(request):
    """Vista para la página de ingresos"""
    # Obtener fecha actual y primer día del mes
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Obtener ingresos del mes actual
    ingresos_list = Ingreso.objects.filter(
        fecha__gte=primer_dia_mes,
        fecha__lte=hoy
    ).order_by('-fecha', '-id')
    
    # Calcular total
    total_ingresos = ingresos_list.aggregate(total=Sum('monto'))['total'] or 0
    
    # Contexto para la plantilla
    context = {
        'ingresos': ingresos_list,
        'total_ingresos': total_ingresos,
        'mes': hoy.strftime('%B %Y')
    }
    
    return render(request, 'core/ingresos.html', context)


def categorias(request):
    """Vista para la página de categorías"""
    categorias = Categoria.objects.all().order_by('nombre')
    
    context = {
        'categorias': categorias
    }
    
    return render(request, 'core/categorias.html', context)


def medios_pago(request):
    """Vista para la página de medios de pago"""
    medios = MedioPago.objects.all().order_by('nombre')
    
    context = {
        'medios': medios
    }
    
    return render(request, 'core/medios_pago.html', context)


def gasto_rapido(request):
    """Vista para la página de gasto rápido (formulario simplificado)"""
    # Obtener categorías y medios de pago para el formulario
    categorias = Categoria.objects.all().order_by('nombre')
    medios_pago = MedioPago.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            concepto = request.POST.get('concepto')
            monto = request.POST.get('monto')
            fecha_str = request.POST.get('fecha')
            categoria_id = request.POST.get('categoria')
            medio_pago_id = request.POST.get('medio_pago')
            observaciones = request.POST.get('observaciones', '')
            
            # Validar datos básicos
            if not all([concepto, monto, fecha_str, categoria_id, medio_pago_id]):
                messages.error(request, 'Todos los campos son requeridos')
                return redirect('/gasto-rapido/')
            
            # Convertir tipos de datos
            try:
                monto = float(monto.replace(',', '.'))
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                categoria = Categoria.objects.get(id=categoria_id)
                medio_pago = MedioPago.objects.get(id=medio_pago_id)
            except (ValueError, Categoria.DoesNotExist, MedioPago.DoesNotExist) as e:
                messages.error(request, f'Error en los datos: {str(e)}')
                return redirect('/gasto-rapido/')
            
            # Crear el gasto
            gasto = Gasto.objects.create(
                concepto=concepto,
                monto=monto,
                categoria=categoria,
                medio_pago=medio_pago,
                fecha=fecha,
                observaciones=observaciones
            )
            
            messages.success(request, f'Gasto "{concepto}" de ${monto} registrado correctamente')
            return redirect('/gasto-rapido/')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el gasto: {str(e)}')
    
    context = {
        'categorias': categorias,
        'medios_pago': medios_pago,
        'fecha_actual': timezone.now().strftime('%Y-%m-%d')
    }
    
    return render(request, 'core/gasto_rapido.html', context)


# Error 404
def handler404(request, exception):
    return render(request, 'core/404.html', status=404)


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
        
        # Crear el gasto
        gasto = Gasto.objects.create(
            concepto=concepto,
            monto=monto,
            fecha=fecha_obj,
            categoria=categoria,
            medio_pago=medio_pago,
            observaciones=observaciones
        )
        
        # Preparar respuesta
        gasto_data = {
            'id': gasto.id,
            'concepto': gasto.concepto,
            'monto': gasto.monto,
            'fecha': gasto.fecha.strftime('%Y-%m-%d'),
            'categoria': {
                'id': gasto.categoria.id,
                'nombre': gasto.categoria.nombre,
                'icon': gasto.categoria.icon,
                'color': gasto.categoria.color
            },
            'medio_pago': {
                'id': gasto.medio_pago.id,
                'nombre': gasto.medio_pago.nombre
            },
            'estado': gasto.estado
        }
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Gasto creado exitosamente',
            'gasto': gasto_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_gasto(request, gasto_id):
    """Elimina un gasto por su ID"""
    try:
        # Obtener el gasto
        gasto = get_object_or_404(Gasto, id=gasto_id)
        gasto.delete()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Gasto eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar el gasto: {str(e)}'}, status=500)


@require_POST
def cambiar_estado_gasto(request, gasto_id):
    """Cambia el estado de un gasto (pendiente/pagado)"""
    try:
        # Obtener datos
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado not in ['pendiente', 'pagado']:
            return JsonResponse({'error': 'Estado inválido'}, status=400)
        
        # Obtener el gasto
        gasto = get_object_or_404(Gasto, id=gasto_id)
        gasto.estado = nuevo_estado
        gasto.save()
        
        mensaje = f'Estado cambiado a {nuevo_estado}'
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al cambiar estado: {str(e)}'}, status=500)


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
        
        # Crear el ingreso
        ingreso = Ingreso.objects.create(
            concepto=concepto,
            monto=monto,
            fecha=fecha_obj,
            categoria=categoria,
            medio_pago=medio_pago,
            observaciones=observaciones
        )
        
        # Preparar datos para la respuesta
        ingreso_data = {
            'id': ingreso.id,
            'concepto': ingreso.concepto,
            'monto': ingreso.monto,
            'fecha': ingreso.fecha.strftime('%Y-%m-%d'),
            'categoria': {
                'id': ingreso.categoria.id,
                'nombre': ingreso.categoria.nombre
            },
            'medio_pago': {
                'id': ingreso.medio_pago.id,
                'nombre': ingreso.medio_pago.nombre
            }
        }
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Ingreso creado exitosamente',
            'ingreso': ingreso_data
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
        return JsonResponse({'error': f'Error al eliminar el ingreso: {str(e)}'}, status=500)


@require_GET
def listar_medios_pago(request):
    """Retorna la lista de medios de pago disponibles"""
    try:
        medios = MedioPago.objects.all().order_by('nombre')
        
        medios_data = [{
            'id': medio.id,
            'nombre': medio.nombre
        } for medio in medios]
        
        return JsonResponse({
            'success': True,
            'medios': medios_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def crear_medio_pago(request):
    """Crea un nuevo medio de pago"""
    try:
        # Obtener datos
        nombre = request.POST.get('nombre')
        
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido'}, status=400)
        
        # Crear medio de pago
        medio = MedioPago.objects.create(nombre=nombre)
        
        # Preparar respuesta
        medio_data = {
            'id': medio.id,
            'nombre': medio.nombre
        }
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Medio de pago creado exitosamente',
            'medio': medio_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_medio_pago(request, medio_id):
    """Elimina un medio de pago existente"""
    try:
        medio = get_object_or_404(MedioPago, id=medio_id)
        
        # Verificar si tiene gastos o ingresos asociados
        gastos_count = Gasto.objects.filter(medio_pago=medio).count()
        ingresos_count = Ingreso.objects.filter(medio_pago=medio).count()
        
        if gastos_count > 0 or ingresos_count > 0:
            return JsonResponse({
                'error': f'No se puede eliminar el medio de pago porque tiene {gastos_count} gastos y {ingresos_count} ingresos asociados'
            }, status=400)
        
        # Si no tiene asociaciones, eliminar
        medio.delete()
        accion = 'eliminado'
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Medio de pago {accion} exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar medio de pago: {str(e)}'}, status=500)


@require_POST
def crear_categoria(request):
    """Crea una nueva categoría"""
    try:
        # Obtener datos
        nombre = request.POST.get('nombre')
        icon = request.POST.get('icon', 'tag')  # Icono predeterminado
        color = request.POST.get('color', '#6c757d')  # Color predeterminado
        
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido'}, status=400)
        
        # Crear categoría
        categoria = Categoria.objects.create(
            nombre=nombre,
            icon=icon,
            color=color
        )
        
        # Preparar respuesta
        categoria_data = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'icon': categoria.icon,
            'color': categoria.color
        }
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Categoría creada exitosamente',
            'categoria': categoria_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def eliminar_categoria(request, categoria_id):
    """Elimina una categoría existente"""
    try:
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        # Verificar si tiene gastos o ingresos asociados
        gastos_count = Gasto.objects.filter(categoria=categoria).count()
        ingresos_count = Ingreso.objects.filter(categoria=categoria).count()
        
        if gastos_count > 0 or ingresos_count > 0:
            return JsonResponse({
                'error': f'No se puede eliminar la categoría porque tiene {gastos_count} gastos y {ingresos_count} ingresos asociados'
            }, status=400)
        
        # Si no tiene asociaciones, eliminar
        categoria.delete()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Categoría eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar categoría: {str(e)}'}, status=500)
