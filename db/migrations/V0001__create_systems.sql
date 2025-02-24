create table if not exists systems
(
    "id"                           integer,
    "name"                         text,
    "x"                            real,
    "y"                            real,
    "z"                            real,
    "population"                   integer,
    "government"                   text,
    "allegiance"                   text,
    "security"                     text,
    "primary_economy"              text,
    "controlling_minor_faction_id" integer,
    "controlling_minor_faction"    text
);
