#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $APP_USER WITH ENCRYPTED PASSWORD '$APP_USER_PWD';
    CREATE DATABASE $APP_DB_NAME;
    GRANT ALL PRIVILEGES ON DATABASE $APP_DB_NAME TO $APP_USER;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$APP_USER" --dbname "$APP_DB_NAME" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS "$APP_SCHEMA";
EOSQL