#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"

fi

sleep 3

python /usr/src/admin_panel/manage.py flush --no-input
python /usr/src/admin_panel/manage.py migrate --fake billing 0001
python /usr/src/admin_panel/manage.py migrate
python /usr/src/admin_panel/manage.py collectstatic --no-input --clear

exec "$@"
