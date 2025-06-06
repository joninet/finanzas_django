#!/usr/bin/env python3
import os
import re

def eliminar_referencias_google_sheets(archivo):
    """Elimina todas las referencias a Google Sheets en un archivo Python"""
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Eliminar importaciones relacionadas con Google Sheets
    contenido = re.sub(r'from \.google_sheets.*\n', '', contenido)
    
    # Eliminar bloques de sincronización
    contenido = re.sub(r'# Sincronizar con Google Sheets[^}]*?sync_[^}]*?}', 
                       'return JsonResponse({\n            \'success\': True,\n            \'mensaje\': \'Operación completada exitosamente\'\n        })', 
                       contenido, flags=re.DOTALL)
    
    # Eliminar variables y comentarios relacionados
    contenido = re.sub(r'sync_result.*\n', '', contenido)
    contenido = re.sub(r'sync_message.*\n', '', contenido)
    contenido = re.sub(r'sync_success.*\n', '', contenido)
    
    # Eliminar llamadas a funciones de sincronización
    contenido = re.sub(r'try:.*?sync_.*?except.*?}\)', 
                       'return JsonResponse({\n            \'success\': True,\n            \'mensaje\': \'Operación completada exitosamente\'\n        })', 
                       contenido, flags=re.DOTALL)
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"Se eliminaron referencias a Google Sheets en {archivo}")

def eliminar_referencias_en_templates(archivo):
    """Elimina referencias a Google Sheets en plantillas HTML"""
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Eliminar elementos HTML relacionados con sincronización
    contenido = re.sub(r'<li.*?sincronizacion_sheets.*?</li>', '<!-- Sincronización eliminada -->', contenido)
    contenido = re.sub(r'<div.*?sync.*?</div>', '', contenido)
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"Se eliminaron referencias a Google Sheets en {archivo}")

def eliminar_sincronizacion_urls(archivo):
    """Elimina URLs relacionadas con sincronización"""
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Eliminar URLs relacionadas con sheets
    contenido = re.sub(r'path\(\'api/sheets/.*\),', '', contenido)
    contenido = re.sub(r'path\(\'sync-sheets/.*\),', '', contenido)
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"Se eliminaron URLs relacionadas con Google Sheets en {archivo}")

if __name__ == '__main__':
    # Limpiar views.py
    eliminar_referencias_google_sheets('/home/joninet/Documentos/git_personal/finanzas_django/core/views.py')
    
    # Limpiar urls.py
    eliminar_sincronizacion_urls('/home/joninet/Documentos/git_personal/finanzas_django/core/urls.py')
    
    # Limpiar plantillas
    for root, dirs, files in os.walk('/home/joninet/Documentos/git_personal/finanzas_django/core/templates'):
        for file in files:
            if file.endswith('.html'):
                eliminar_referencias_en_templates(os.path.join(root, file))
                
    print("Limpieza completada. La aplicación ahora utiliza únicamente SQLite.")
