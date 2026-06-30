#!/bin/bash
set -e

echo "Waiting for postgres..."
until python -c "import psycopg2; psycopg2.connect(
    dbname='$DB_NAME',
    user='$DB_USER',
    password='$DB_PASSWORD',
    host='$DB_HOST',
    port='$DB_PORT'
)" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is up."

python manage.py migrate --noinput
exec "$@"
