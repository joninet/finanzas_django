#!/usr/bin/env python
"""
Script para corregir el formato de fecha en las funciones crear_gasto y crear_ingreso
"""

import os
import re

def fix_date_format_in_file(file_path):
    # Leer contenido actual
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Patrón para buscar bloques de código de conversión de fecha
    pattern = r"# Convertir fecha\s+try:\s+fecha_obj = datetime\.strptime\(fecha, '%d/%m/%Y'\)\.date\(\)\s+except ValueError:\s+return JsonResponse\(\{'error': 'Formato de fecha inválido'\}, status=400\)"
    
    # Código de reemplazo que admite ambos formatos
    replacement = """# Convertir fecha
        try:
            try:
                # Intentar primero con formato ISO (YYYY-MM-DD) del input type="date"
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                # Si falla, intentar con formato dd/mm/yyyy
                fecha_obj = datetime.strptime(fecha, '%d/%m/%Y').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido. Use YYYY-MM-DD o DD/MM/YYYY'}, status=400)"""
    
    # Reemplazar en el contenido
    modified_content = re.sub(pattern, replacement, content)
    
    # Guardar cambios
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    return "Formato de fecha actualizado correctamente"

if __name__ == "__main__":
    # Ruta al archivo views.py
    views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'views.py')
    result = fix_date_format_in_file(views_path)
    print(result)
