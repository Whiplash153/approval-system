#!/bin/bash
set -e

: "${POSTGRES_TEST_DB:?POSTGRES_TEST_DB is not set}"

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=test_db="$POSTGRES_TEST_DB" <<-'EOSQL'
SELECT format('CREATE DATABASE %I', :'test_db')
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = :'test_db'
)\gexec
EOSQL
