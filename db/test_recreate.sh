#!/usr/bin/env bash

DB=./tests/test_workspace/spyplane.db

rm -rf "$DB"
sqlite3 "$DB" < ./db/schema.sql
sqlite3 "$DB" < ./db/data/import.sql
