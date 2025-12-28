# SpyPlane

Scouting bot

# Functional Notes

[Link to Notes](https://docs.google.com/document/d/1a4U9vYSLk9_sQVjA3xz49KnCS0hibOq2ELEXc87X9yI/edit?usp=sharing)

# Tech Notes

## Local devbox setup

### Option 1: Modern uv approach (recommended)
1. Install [uv using instructions here](https://github.com/astral-sh/uv#installation)
2. Install dependencies: `uv sync`
3. Copy `.env.sample` to `.env` and update the values for TEST and PROD
4. **Create the database**: `./db/recreate.sh`
5. **Seed with test data**: `cd db/data && uv run python seed_database.py`
6. Startup the bot with `uv run spy` or `uv run python -m spyplane.spy_plane`

### Option 2: Manual virtual environment
1. Install [uv using instructions here](https://github.com/astral-sh/uv#installation)
2. Create a virtual environment: `uv venv`
3. Activate the virtual environment: `source .venv/bin/activate`
4. Install dependencies: `uv pip sync requirements.lock`
5. Copy `.env.sample` to `.env` and update the values for TEST and PROD
6. **Create the database**: `./db/recreate.sh`
7. **Seed with test data**: `cd db/data && python seed_database.py`
8. Startup the bot with `uv run spy` or `uv run python -m spyplane.spy_plane`

## System Tracking

The bot now tracks systems directly in the SQLite database. Use the following Discord commands:

- `/faction_track <system_name> <priority>` - Add a system to track (Primary, Secondary, or Tertiary)
- `/faction_remove <system_name>` - Remove a system from tracking  
- `/faction_list` - List all currently tracked systems

**Note**: Systems are validated against the `systems` table when added via `/faction_track`. Only valid systems can be tracked.

## Running tests

From the repo root

```bash
# Using uv (recommended)
uv run python -m unittest discover tests -v

# Or using python directly
python -m unittest
```


## Example docker deployment
```bash
#!/usr/bin/env bash
set -eux

docker pull asia.gcr.io/pilotstradenetwork/spyplane:latest

docker stop spyplane_flight || true && docker rm spyplane_flight || true

# If you face permissions during pull in gcloud VM, just run `docker-credential-gcr configure-docker`

cat /spy/env.list

docker run \
        -d \
        -v /spy/workspace:/app/workspace \
        -e DB_RECREATE \
        --env-file /spy/env.list \
        --name spyplane_flight \
        --restart unless-stopped \
        asia.gcr.io/pilotstradenetwork/spyplane:latest

echo 'Spyplane deployment done!'
```

