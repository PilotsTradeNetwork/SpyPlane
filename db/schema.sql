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
    "goalkind"     TEXT NOT NULL,
    "additional_note" TEXT
);

CREATE TABLE IF NOT EXISTS faction_header_footer
(
    id INTEGER PRIMARY KEY CHECK (id = 1),
    header TEXT,
    footer TEXT
);

INSERT INTO faction_header_footer (id, header, footer)
VALUES (1, '__Current Short Term Goals__', '**__Note__:** Ensure you assess the system you are working in before performing any contribution.

If a conflict is **pending** do not perform any actions for the faction (Your effort will have no effect).
If a conflict is **active** refer to <#885511659022598145> for direction on how to contribute.

If anything has happened that isn''t in <#878535931580284928> **__do not engage__**, ask for further direction in <#878738588647436288> from our faction team. (e.g, if an unexpected war/election occurs in a system we are working)

*Last Updated <t:{}:D>*')
ON CONFLICT(id) DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('interval_hours', '4', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('carryover', 'true', 1655665882)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp)
VALUES ('daily_interval_hours', '12', 1658255653)
ON CONFLICT DO NOTHING;

INSERT INTO configuration (name, value, timestamp) VALUES ('primary_limit',   '0', 1655665882) ON CONFLICT DO NOTHING;
INSERT INTO configuration (name, value, timestamp) VALUES ('secondary_limit',  '0', 1655665882) ON CONFLICT DO NOTHING;
INSERT INTO configuration (name, value, timestamp) VALUES ('tertiary_limit',   '0', 1655665882) ON CONFLICT DO NOTHING;
INSERT INTO configuration (name, value, timestamp) VALUES ('selection_mode',   'oldest_first', 1655665882) ON CONFLICT DO NOTHING;
INSERT INTO configuration (name, value, timestamp) VALUES ('tracked_changed_at', '0', 1655665882) ON CONFLICT DO NOTHING;
