# Changelog
## 2.1.0
- [#54](https://github.com/PilotsTradeNetwork/SpyPlane/pull/54) Sort posted systems by shortest route (IndorilReborn)
- [#55](https://github.com/PilotsTradeNetwork/SpyPlane/pull/55) Order `oldest_first` selection by last scout time (IndorilReborn)

## 2.0.2
- Properly count scouted systems for the current tick
- Fix posted counts by soft-deleting scouted systems
- Add `/faction refresh_progress` command

## 2.0.1
- Simplify goals flow, improve adding goals UX

# 2.0.0
- Full rework, remove EBGS/Sheets, rely on EDDN for scouting

## 0.0.6
- Make sheet sync response ephemeral

## 0.0.5
- [#44](https://github.com/PilotsTradeNetwork/SpyPlane/pull/44) Remove 100 message limit from scouting purge (IndorilReborn)
- [#45](https://github.com/PilotsTradeNetwork/SpyPlane/pull/45) Add link to first scouting system (IndorilReborn)
- [#41](https://github.com/PilotsTradeNetwork/SpyPlane/pull/41) Wrap tick check call in try/except to prevent task failure (IndorilReborn)

## 0.0.4
- update dependencies
- zip systems file
- add all bubble systems to database

## 0.0.3
- updated tick source
- changed docker base

## 0.0.2
- various and sundry dependabot updates
- add prometheus logging (IndorilReborn)

## 0.0.1
- make bot
