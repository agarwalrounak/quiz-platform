#!/bin/sh
set -e

# Wait for MySQL to accept connections (skipped when using sqlite).
if [ "${DB_ENGINE:-mysql}" != "sqlite" ]; then
  echo "Waiting for MySQL at ${MYSQL_HOST:-db}:${MYSQL_PORT:-3306}..."
  while ! nc -z "${MYSQL_HOST:-db}" "${MYSQL_PORT:-3306}"; do
    sleep 1
  done
  echo "MySQL is up."
fi

echo "Applying migrations..."
python manage.py migrate --noinput

# Optionally seed the question bank (Milestone 4 command). Safe no-op until then.
if [ "${SEED_ON_START:-false}" = "true" ]; then
  python manage.py seed_questions || echo "seed_questions not available yet; skipping."
fi

echo "Starting server..."
exec "$@"
