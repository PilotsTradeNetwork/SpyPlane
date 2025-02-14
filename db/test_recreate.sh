#!/usr/bin/env bash

DB=./tests/test_workspace/spyplane.db

rm -rf "$DB"
for file in ./db/migrations/*.sql; do
  sqlite3 "$DB" < "$file"
done
sqlite3 "$DB" < ./db/data/spyplane_import.sql
