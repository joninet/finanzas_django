#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Running migrations..."
cd finanzas_django
python manage.py migrate --noinput

echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

echo "Starting gunicorn..."
gunicorn finanzas_personales.wsgi:application