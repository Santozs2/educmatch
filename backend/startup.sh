#!/bin/bash
# Inicialização no Azure App Service (Linux). Os seeds usam update_or_create,
# então rodar a cada boot não duplica nada.
set -e
cd "$(dirname "$0")"

mkdir -p /home/data

python manage.py migrate --noinput
python manage.py createcachetable
python manage.py seed_areas
python manage.py seed_cursos
python manage.py seed_questoes
python manage.py seed_avaliacao
python manage.py collectstatic --noinput

exec gunicorn core.wsgi:application --bind=0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
