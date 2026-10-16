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

# gthread: a chamada à LLM é espera de rede, e com threads um worker atende
# outros alunos enquanto espera. 2 workers x 8 threads = 16 quizzes ao mesmo
# tempo (com o worker síncrono eram 2).
exec gunicorn core.wsgi:application --bind=0.0.0.0:${PORT:-8000} \
    --worker-class gthread --workers ${GUNICORN_WORKERS:-2} --threads ${GUNICORN_THREADS:-8} \
    --timeout 120
