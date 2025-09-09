#!/usr/bin/env bash

DB=./tests/test_workspace/spyplane.db

rm -rf "$DB"
sqlite3 "$DB" < ./db/schema.sql
7zr x -y db/data/system_names.csv.7z -odb/data/
sqlite3 "$DB" < ./db/data/import.sql
