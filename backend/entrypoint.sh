#!/bin/sh

echo "Running database migrations..."
alembic upgrade head

echo "Starting application server..."
exec gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
