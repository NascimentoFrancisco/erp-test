#!/bin/bash
set -e

echo "Applying migrations..."
python src/manage.py migrate

if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ]; then
  if [ "$AUTO_SEED_ON_STARTUP" = "False" ] || [ "$AUTO_SEED_ON_STARTUP" = "false" ]; then
    echo "Skipping seed (AUTO_SEED_ON_STARTUP=false)..."
  else
    echo "Applying initial development seed..."
    python src/manage.py seed_initial_data
  fi
fi

echo "Collecting static files..."
python src/manage.py collectstatic --noinput

echo "Starting server..."
exec python src/manage.py runserver 0.0.0.0:8000
