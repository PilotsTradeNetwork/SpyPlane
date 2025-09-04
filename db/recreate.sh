#!/usr/bin/env bash

DB=./workspace/spyplane.db

rm -rf "$DB"
sqlite3 "$DB" < ./db/schema.sql
sqlite3 "$DB" < ./db/data/import.sql
