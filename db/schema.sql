CREATE TABLE IF NOT EXISTS systems (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS scout_systems
(
    "system_name" TEXT PRIMARY KEY,
    "priority"    TEXT NOT NULL,
    "added_by"    TEXT NOT NULL,
    "added_at"    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scout_history
(
    "id"          INTEGER PRIMARY KEY AUTOINCREMENT,
    "system_name" TEXT NOT NULL,
    "username"    TEXT NOT NULL,
    "userid"      INTEGER NOT NULL,
    "timestamp"   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS configuration
(
    "id"        INTEGER PRIMARY KEY AUTOINCREMENT,
    "name"      TEXT    NOT NULL,
    "value"     TEXT    NOT NULL,
    "timestamp" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scout_systems_posted
(
    "system_name" TEXT PRIMARY KEY,
    "priority"    TEXT NOT NULL,
    "message_id"  INTEGER
);

CREATE TABLE IF NOT EXISTS faction_states
(
    "system"      TEXT NOT NULL,
    "faction"     TEXT NOT NULL,
    "active_csv"  TEXT NOT NULL,
    "pending_csv" TEXT NOT NULL,
    "influence"   REAL,
    "controlling" INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY ("system", "faction")
);

CREATE TABLE IF NOT EXISTS faction_goals
(
    "index"        INTEGER PRIMARY KEY,
    "system"       TEXT NOT NULL,
    "faction_one"  TEXT NOT NULL,
    "faction_other" TEXT NOT NULL,
    "goalkind"     TEXT NOT NULL
);

INSERT INTO configuration (name, value, timestamp)
VALUES ('interval_hours', '4', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('carryover', 'true', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('daily_interval_hours', '12', 1658255653)
ON CONFLICT DO NOTHING;