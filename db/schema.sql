-- Final schema for the systems table
DROP TABLE IF EXISTS systems;
CREATE TABLE systems (
    name TEXT PRIMARY KEY
);

-- Final schema for the scout_systems table
DROP TABLE IF EXISTS scout_systems;
CREATE TABLE scout_systems
(
    "system_name" TEXT PRIMARY KEY,
    "priority"    TEXT NOT NULL,
    "added_by"    TEXT NOT NULL,
    "added_at"    INTEGER NOT NULL
);

-- Schema for the scout_history table
CREATE TABLE IF NOT EXISTS scout_history
(
    "id"          INTEGER PRIMARY KEY AUTOINCREMENT,
    "system_name" TEXT NOT NULL,
    "username"    TEXT NOT NULL,
    "userid"      INTEGER NOT NULL,
    "timestamp"   INTEGER NOT NULL
);

-- Schema for the configuration table
CREATE TABLE IF NOT EXISTS configuration
(
    "id"        INTEGER PRIMARY KEY AUTOINCREMENT,
    "name"      TEXT    NOT NULL,
    "value"     TEXT    NOT NULL,
    "timestamp" INTEGER NOT NULL
);

-- Schema for the scout_systems_posted table
CREATE TABLE IF NOT EXISTS scout_systems_posted
(
    "system_name" TEXT PRIMARY KEY,
    "priority"    TEXT NOT NULL
);

-- Consolidated inserts for the configuration table
INSERT INTO configuration (name, value, timestamp)
VALUES ('interval_hours', '4', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('carryover', 'true', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('daily_interval_hours', '12', 1658255653)
ON CONFLICT DO NOTHING;