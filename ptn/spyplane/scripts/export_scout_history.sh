#!/usr/bin/env bash
set -eux
sqlite3 ./workspace/spyplane.db < ./ptn/spyplane/scripts/export.sql
