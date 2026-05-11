# SpyPlane

Scouting bot

## Documentation

- [Faction Goals Commands](docs/FACTION_GOALS.md) - Documentation for managing faction goals (add, remove, post, embed, list)
- [Faction Tracking Commands](docs/FACTION_TRACKING.md) - Documentation for tracking systems, EDDN listener, and reporting

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
7. **Create the database**: `bash db/recreate.sh`
8. **Seed with test data**: `cd db/data && uv run python seed_database.py`
9. Startup the bot with `uv run spy` or `uv run python -m ptn.spyplane.spy_plane`

## Running tests

From the repo root:

```bash
bash db/test_recreate.sh
uv run python -m unittest discover tests -v
```

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
