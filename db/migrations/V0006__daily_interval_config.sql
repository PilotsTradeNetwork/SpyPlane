insert into configuration (name, value, timestamp)
values ('daily_interval_hours', '12', 1658255653)
on conflict do nothing;
