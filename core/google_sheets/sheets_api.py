"""
Módulo para interactuar con la API de Google Sheets
Este módulo permite sincronizar datos entre la aplicación Django y Google Sheets
"""

import os
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.models import Movimiento, Gasto, Ingreso, Categoria, MedioPago


# Configuración de la API de Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GASTOS_SHEET_ID = getattr(settings, 'GASTOS_SHEET_ID', '')
INGRESOS_SHEET_ID = getattr(settings, 'INGRESOS_SHEET_ID', '')
CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')


def get_sheets_service():
    """
    Obtiene un servicio autorizado para interactuar con la API de Google Sheets
    """
    try:
        # Verificar si existe el archivo de credenciales
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(f"Archivo de credenciales no encontrado: {CREDENTIALS_FILE}")
        
        # Cargar credenciales desde el archivo JSON descargado de Google Cloud Console
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
            
        # Construir el servicio
        service = build('sheets', 'v4', credentials=credentials)
        
        return service
    except Exception as e:
        print(f"Error al crear el servicio de Google Sheets: {e}")
        return None


def sync_gastos_to_sheets():
    """
    Sincroniza los gastos desde la base de datos hacia Google Sheets
    """
    if not GASTOS_SHEET_ID:
        return {'error': 'No se ha configurado el ID de la hoja de gastos'}
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'No se pudo establecer conexión con Google Sheets'}
            
        # Obtener todos los gastos
        gastos = Gasto.objects.all().order_by('-fecha', '-id')
        
        # Preparar los datos para la hoja
        header = ['ID', 'Fecha', 'Concepto', 'Monto', 'Categoría', 'Medio de Pago', 'Estado', 'Tipo']
        values = [header]
        
        for gasto in gastos:
            # Manejar el caso cuando categoria y medio_pago son strings u objetos
            if hasattr(gasto.categoria, 'nombre'):
                categoria_nombre = gasto.categoria.nombre
            else:
                categoria_nombre = str(gasto.categoria) if gasto.categoria else ''
                
            if hasattr(gasto.medio_pago, 'nombre'):
                medio_pago_nombre = gasto.medio_pago.nombre
            else:
                medio_pago_nombre = str(gasto.medio_pago) if gasto.medio_pago else ''
            
            values.append([
                str(gasto.id),
                gasto.fecha.strftime('%Y-%m-%d'),
                gasto.concepto,
                str(gasto.monto),
                categoria_nombre,
                medio_pago_nombre,
                gasto.estado,
                'Gasto'
            ])
        
        # Actualizar la hoja
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=GASTOS_SHEET_ID,
            range='Gastos!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return {
            'success': True,
            'message': f'Sincronizados {result.get("updatedCells")} celdas de gastos'
        }
        
    except HttpError as error:
        return {'error': f'Error en la API: {error}'}
    except Exception as e:
        return {'error': f'Error al sincronizar gastos: {e}'}


def sync_ingresos_to_sheets():
    """
    Sincroniza los ingresos desde la base de datos hacia Google Sheets
    """
    if not INGRESOS_SHEET_ID:
        return {'error': 'No se ha configurado el ID de la hoja de ingresos'}
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'No se pudo establecer conexión con Google Sheets'}
            
        # Obtener todos los ingresos
        ingresos = Ingreso.objects.all().order_by('-fecha', '-id')
        
        # Preparar los datos para la hoja
        header = ['ID', 'Fecha', 'Concepto', 'Monto', 'Categoría', 'Medio de Pago', 'Tipo']
        values = [header]
        
        for ingreso in ingresos:
            # Manejar el caso cuando categoria y medio_pago son strings u objetos
            if hasattr(ingreso.categoria, 'nombre'):
                categoria_nombre = ingreso.categoria.nombre
            else:
                categoria_nombre = str(ingreso.categoria) if ingreso.categoria else ''
                
            if hasattr(ingreso.medio_pago, 'nombre'):
                medio_pago_nombre = ingreso.medio_pago.nombre
            else:
                medio_pago_nombre = str(ingreso.medio_pago) if ingreso.medio_pago else ''
            
            values.append([
                str(ingreso.id),
                ingreso.fecha.strftime('%Y-%m-%d'),
                ingreso.concepto,
                str(ingreso.monto),
                categoria_nombre,
                medio_pago_nombre,
                'Ingreso'
            ])
        
        # Actualizar la hoja
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=INGRESOS_SHEET_ID,
            range='Ingresos!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return {
            'success': True,
            'message': f'Sincronizados {result.get("updatedCells")} celdas de ingresos'
        }
        
    except HttpError as error:
        return {'error': f'Error en la API: {error}'}
    except Exception as e:
        return {'error': f'Error al sincronizar ingresos: {e}'}


def sync_medios_pago_to_sheets():
    """
    Sincroniza los medios de pago desde la base de datos hacia Google Sheets
    """
    if not GASTOS_SHEET_ID:  # Usamos la misma hoja que gastos
        return {'error': 'No se ha configurado el ID de la hoja de gastos'}
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'No se pudo establecer conexión con Google Sheets'}
            
        # Obtener todos los medios de pago
        medios_pago = MedioPago.objects.all().order_by('nombre')
        
        # Preparar los datos para la hoja
        header = ['ID', 'Nombre', 'Descripción', 'Estado']
        values = [header]
        
        for medio in medios_pago:
            values.append([
                str(medio.id),
                medio.nombre,
                medio.descripcion if hasattr(medio, 'descripcion') else '',
                'Activo' if medio.activo else 'Inactivo'
            ])
        
        # Actualizar la hoja
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=GASTOS_SHEET_ID,
            range='MediosPago!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return {
            'success': True,
            'message': f'Sincronizados {result.get("updatedCells")} celdas de medios de pago'
        }
        
    except HttpError as error:
        return {'error': f'Error en la API: {error}'}
    except Exception as e:
        return {'error': f'Error al sincronizar medios de pago: {e}'}


def sync_categorias_to_sheets():
    """
    Sincroniza las categorías desde la base de datos hacia Google Sheets
    """
    if not GASTOS_SHEET_ID:  # Usamos la misma hoja que gastos
        return {'error': 'No se ha configurado el ID de la hoja de gastos'}
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'No se pudo establecer conexión con Google Sheets'}
            
        # Obtener todas las categorías
        categorias = Categoria.objects.all().order_by('nombre')
        
        # Preparar los datos para la hoja
        header = ['ID', 'Nombre', 'Descripción', 'Estado']
        values = [header]
        
        for categoria in categorias:
            values.append([
                str(categoria.id),
                categoria.nombre,
                categoria.descripcion if hasattr(categoria, 'descripcion') else '',
                'Activo' if categoria.activo else 'Inactivo'
            ])
        
        # Actualizar la hoja
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=GASTOS_SHEET_ID,
            range='Categorias!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return {
            'success': True,
            'message': f'Sincronizados {result.get("updatedCells")} celdas de categorías'
        }
        
    except HttpError as error:
        return {'error': f'Error en la API: {error}'}
    except Exception as e:
        return {'error': f'Error al sincronizar categorías: {e}'}


def import_from_sheets():
    """
    Importa datos desde Google Sheets a la base de datos
    """
    results = {}
    
    # Importar gastos
    if GASTOS_SHEET_ID:
        try:
            service = get_sheets_service()
            if not service:
                results['gastos'] = {'error': 'No se pudo establecer conexión con Google Sheets'}
            else:
                # Obtener datos de la hoja
                result = service.spreadsheets().values().get(
                    spreadsheetId=GASTOS_SHEET_ID,
                    range='Gastos!A2:H'  # Desde la fila 2 (sin encabezados) hasta columna H
                ).execute()
                
                rows = result.get('values', [])
                if not rows:
                    results['gastos'] = {'message': 'No se encontraron datos en la hoja de gastos'}
                else:
                    gastos_importados = 0
                    
                    for row in rows:
                        # Asegurarse de que haya suficientes columnas
                        if len(row) >= 7:  # Mínimo debe tener hasta la columna del estado
                            try:
                                # ID en Google Sheets (si existe)
                                sheet_id = row[0] if row[0] else None
                                
                                # Buscar o crear categoría
                                categoria = None
                                if len(row) > 4 and row[4]:
                                    categoria, _ = Categoria.objects.get_or_create(
                                        nombre=row[4], 
                                        defaults={'tipo': 'gasto'}
                                    )
                                
                                # Buscar o crear medio de pago
                                medio_pago = None
                                if len(row) > 5 and row[5]:
                                    medio_pago, _ = MedioPago.objects.get_or_create(nombre=row[5])
                                
                                # Estado por defecto
                                estado = 'pendiente'
                                if len(row) > 6 and row[6] in ['pendiente', 'pagado', 'cancelado']:
                                    estado = row[6]
                                
                                # Verificar si ya existe este gasto
                                if sheet_id and sheet_id.isdigit():
                                    gasto = Gasto.objects.filter(id=int(sheet_id)).first()
                                    
                                    if gasto:
                                        # Actualizar el gasto existente
                                        gasto.fecha = row[1]
                                        gasto.concepto = row[2]
                                        gasto.monto = float(row[3])
                                        gasto.categoria = categoria
                                        gasto.medio_pago = medio_pago
                                        gasto.estado = estado
                                        gasto.save()
                                    else:
                                        # Crear un nuevo gasto
                                        Gasto.objects.create(
                                            fecha=row[1],
                                            concepto=row[2],
                                            monto=float(row[3]),
                                            categoria=categoria,
                                            medio_pago=medio_pago,
                                            estado=estado
                                        )
                                else:
                                    # Crear un nuevo gasto (sin ID)
                                    Gasto.objects.create(
                                        fecha=row[1],
                                        concepto=row[2],
                                        monto=float(row[3]),
                                        categoria=categoria,
                                        medio_pago=medio_pago,
                                        estado=estado
                                    )
                                    
                                gastos_importados += 1
                            except Exception as e:
                                print(f"Error al importar fila de gasto: {e}")
                                continue
                                
                    results['gastos'] = {
                        'success': True,
                        'message': f'Importados {gastos_importados} gastos desde Google Sheets'
                    }
        except Exception as e:
            results['gastos'] = {'error': f'Error al importar gastos: {e}'}
    
    # Importar ingresos
    if INGRESOS_SHEET_ID:
        try:
            service = get_sheets_service()
            if not service:
                results['ingresos'] = {'error': 'No se pudo establecer conexión con Google Sheets'}
            else:
                # Obtener datos de la hoja
                result = service.spreadsheets().values().get(
                    spreadsheetId=INGRESOS_SHEET_ID,
                    range='Ingresos!A2:G'  # Desde la fila 2 (sin encabezados) hasta columna G
                ).execute()
                
                rows = result.get('values', [])
                if not rows:
                    results['ingresos'] = {'message': 'No se encontraron datos en la hoja de ingresos'}
                else:
                    ingresos_importados = 0
                    
                    for row in rows:
                        # Asegurarse de que haya suficientes columnas
                        if len(row) >= 4:  # Mínimo debe tener monto
                            try:
                                # ID en Google Sheets (si existe)
                                sheet_id = row[0] if row[0] else None
                                
                                # Buscar o crear categoría
                                categoria = None
                                if len(row) > 4 and row[4]:
                                    categoria, _ = Categoria.objects.get_or_create(
                                        nombre=row[4], 
                                        defaults={'tipo': 'ingreso'}
                                    )
                                
                                # Buscar o crear medio de pago
                                medio_pago = None
                                if len(row) > 5 and row[5]:
                                    medio_pago, _ = MedioPago.objects.get_or_create(nombre=row[5])
                                
                                # Verificar si ya existe este ingreso
                                if sheet_id and sheet_id.isdigit():
                                    ingreso = Ingreso.objects.filter(id=int(sheet_id)).first()
                                    
                                    if ingreso:
                                        # Actualizar el ingreso existente
                                        ingreso.fecha = row[1]
                                        ingreso.concepto = row[2]
                                        ingreso.monto = float(row[3])
                                        ingreso.categoria = categoria
                                        ingreso.medio_pago = medio_pago
                                        ingreso.save()
                                    else:
                                        # Crear un nuevo ingreso
                                        Ingreso.objects.create(
                                            fecha=row[1],
                                            concepto=row[2],
                                            monto=float(row[3]),
                                            categoria=categoria,
                                            medio_pago=medio_pago
                                        )
                                else:
                                    # Crear un nuevo ingreso (sin ID)
                                    Ingreso.objects.create(
                                        fecha=row[1],
                                        concepto=row[2],
                                        monto=float(row[3]),
                                        categoria=categoria,
                                        medio_pago=medio_pago
                                    )
                                    
                                ingresos_importados += 1
                            except Exception as e:
                                print(f"Error al importar fila de ingreso: {e}")
                                continue
                                
                    results['ingresos'] = {
                        'success': True,
                        'message': f'Importados {ingresos_importados} ingresos desde Google Sheets'
                    }
        except Exception as e:
            results['ingresos'] = {'error': f'Error al importar ingresos: {e}'}
    
    return results
