#!/usr/bin/env bash

DB=./ptn/data/spyplane.db

rm -rf "$DB"
sqlite3 "$DB" < ./db/schema.sql
7zr x -y db/data/system_names.csv.7z -odb/data/
sqlite3 "$DB" < ./db/data/import.sql
(cd db/data && uv run python seed_database.py)
