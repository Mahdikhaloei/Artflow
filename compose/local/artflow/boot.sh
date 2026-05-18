#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Waiting for PostgreSQL to become available..."
python << END
import sys
import time
import psycopg2

start = time.time()
timeout = 30

while True:
    try:
        conn = psycopg2.connect(
            dbname="${DB_NAME}",
            user="${DB_USER}",
            password="${DB_PASS}",
            host="${DB_HOST}",
            port="${DB_PORT}",
        )
        conn.close()
        break
    except psycopg2.OperationalError as e:
        if time.time() - start > timeout:
            sys.stderr.write(f"PostgreSQL connection timeout: {e}\n")
            sys.exit(1)
        time.sleep(1)
END

echo "PostgreSQL is available"

exec "$@"
