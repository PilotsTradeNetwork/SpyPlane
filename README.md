# SpyPlane

Discord scouting bot for the Pilots Trade Network BGS team (Elite Dangerous). It posts systems to scout, detects
visits via EDDN, tracks faction states and maintains the faction goals embed.

## Documentation

- [Faction Tracking Commands](docs/FACTION_TRACKING.md) - tracked systems, posting, config, EDDN listener, progress embeds, reports
- [Faction Goals Commands](docs/FACTION_GOALS.md) - goals add/edit/remove/list, embed header/footer, posting

## Command Reference

| Command | Description |
|---|---|
| `/faction track` | Edit the full tracked systems list (Primary/Secondary/Tertiary modal) |
| `/faction list` | Export tracked systems as CSV |
| `/faction launch` | Post the scouting list to the scout channel now |
| `/faction config` | Set `interval_hours`, `primary_limit`, `secondary_limit`, `tertiary_limit`, `selection_mode` |
| `/faction config_dump` | Show all config values |
| `/faction refresh_progress` | Force-refresh the scouting progress embeds |
| `/faction daily_report` | Post the faction state report in the current channel |
| `/faction operations_report` | Top scouts of the last 90 days + scout history CSV |
| `/goal add` | Add a goal (Raise INF, Win Conflict, Custom) |
| `/goal edit` | Edit an existing goal |
| `/goal remove` | Remove one or all goals |
| `/goal list` | List all goals |
| `/goal embed` | Edit the goals embed header/footer |
| `/goal post` | Post or update the goals embed |
| `@SpyPlane ping` | Reply with the bot version |

# Functional Notes

[Link to Notes](https://docs.google.com/document/d/1a4U9vYSLk9_sQVjA3xz49KnCS0hibOq2ELEXc87X9yI/edit?usp=sharing)

# Tech Notes

## Local devbox setup

1. Install [uv using instructions here](https://github.com/astral-sh/uv#installation)
2. (Optionally) Install Python: `uv python install`
3. Install dependencies: `uv sync --extra dev`
4. Install uv tools: `uv tool install prek`
5. Install the pre-commit hook: `prek install`
6. Copy `.env.sample` to `.env` and update the values for TEST and PROD
7. **Create and seed the database**: `bash db/recreate.sh` (requires `sqlite3` and `7zr`)
8. Startup the bot with `uv run spy` or `uv run python -m ptn.spyplane.spy_plane`

## Running tests

From the repo root:

```bash
bash db/test_recreate.sh
uv run python -m unittest discover tests -v
```

Or both steps at once: `uv run tests`. `test_post_after_tick_service.py` needs network access.

## Pre-commit checks

Run pre-commit hooks on all files with:

```bash
prek run --all-files
```

## Docker setup

1. Build the image:

```bash
docker build --build-arg VERSION=$(uvx --from setuptools-scm python -m setuptools_scm) -t spyplane .
```

2. Run the container, mounting your workspace directory:

```bash
docker run --rm --name spyplane -v /spy/workspace:/app/workspace --env-file /spy/env.list spyplane
```


## Example docker deployment

```bash
#!/usr/bin/env bash
set -eux

docker pull $REGISTRY/spyplane:latest

docker stop spyplane || true && docker rm spyplane || true

cat /spy/env.list

docker run \
        -d \
        -v /spy/workspace:/app/workspace \
        -e DB_RECREATE \
        --env-file /spy/env.list \
        --name spyplane \
        --restart unless-stopped \
        $REGISTRY/spyplane:latest

echo 'Spyplane deployment done!'
```
