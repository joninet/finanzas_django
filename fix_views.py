#!/usr/bin/env python3

def fix_views_file():
    """
    Limpia el archivo views.py eliminando todas las referencias a Google Sheets
    y corrigiendo errores de sintaxis.
    """
    # Leer el archivo original
    with open('/home/joninet/Documentos/git_personal/finanzas_django/core/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Crear un nuevo contenido
    new_content = []
    
    # Importaciones básicas sin Google Sheets
    new_content.append("""from django.shortcuts import render, redirect, get_object_or_404
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
""")

    # Encontrar y copiar las vistas principales que no tienen referencias a Google Sheets
    in_sync_function = False
    skip_next_lines = 0
    
    for i, line in enumerate(lines):
        # Saltar las primeras líneas (importaciones)
        if i < 20:
            continue
            
        # Detectar funciones de sincronización para saltarlas
        if any(x in line for x in ['sync_', 'sheets_', 'import_from_sheets']):
            in_sync_function = True
            continue
            
        # Si estamos en una función de sincronización y encontramos una nueva función, salimos del modo
        if in_sync_function and line.startswith('def '):
            in_sync_function = False
            
        # Si no estamos en una función de sincronización, agregamos la línea
        if not in_sync_function and skip_next_lines <= 0:
            # Reemplazar bloques de sincronización dentro de funciones normales
            if 'sync_gastos_to_sheets' in line or 'sync_ingresos_to_sheets' in line or 'sync_medios_pago_to_sheets' in line or 'sync_categorias_to_sheets' in line:
                skip_next_lines = 10  # Saltar aproximadamente 10 líneas
                continue
                
            # Reemplazar mensajes de sincronización
            if 'sync_message' in line:
                continue
                
            # Agregar la línea al nuevo contenido
            new_content.append(line)
        else:
            skip_next_lines -= 1
    
    # Escribir el nuevo contenido al archivo
    with open('/home/joninet/Documentos/git_personal/finanzas_django/core/views.py', 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    
    print("El archivo views.py ha sido limpiado correctamente.")

if __name__ == "__main__":
    fix_views_file()
