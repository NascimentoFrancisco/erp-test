#!/bin/bash
set -e

echo "Applying migrations..."
python src/manage.py migrate

echo "Collecting static files..."
python src/manage.py collectstatic --noinput

echo "Starting server..."
exec python src/manage.py runserver 0.0.0.0:8000
