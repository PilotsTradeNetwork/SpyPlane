#!/usr/bin/env bash
set -eux

DB=workspace/spyplane.db

if [[ -z "${DB_RECREATE-}" ]]; then
  echo "Not creating a new DB"
else
  echo "DB_RECREATE: ${DB_RECREATE} is defined, creating a new DB"
  rm -rf "$DB"
  sqlite3 "$DB" < ./db/schema.sql
  7zr x -y db/data/system_names.csv.7z -odb/data/
  sqlite3 "$DB" < ./db/data/import.sql
fi

python -m spyplane.spy_plane
