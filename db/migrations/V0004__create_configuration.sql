create table if not exists configuration
(
    "id"        integer primary key autoincrement,
    "name"      text    not null,
    "value"     text    not null,
    "timestamp" integer not null
);

insert into configuration (name, value, timestamp)
values ('interval_hours', '4', 1655665882)
on conflict do nothing;
