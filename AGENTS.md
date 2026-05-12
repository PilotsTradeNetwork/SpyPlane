# AGENTS.md — Onboarding Guide for AI Coding Agents

Trust the instructions in this file. Only perform additional exploration if you
find information here to be incomplete or incorrect for the specific change you
are making.

---

## What This Repository Does

SpyPlane is a **Discord bot** for the Pilots Trade Network (PTN) community. It
supports the in-game BGS (Background Simulation) faction management activities
for the space game *Elite Dangerous*. Key responsibilities:

- Tracks star systems that need scouting and posts them to a Discord channel.
- Listens to the **EDDN** (Elite Dangerous Data Network) ZMQ stream to
  automatically record scouts when a player visits a tracked system.
- Manages faction **goals** (add/remove/post/embed) visible to Discord members.
- Reads faction influence and state data from EDDN events and stores them in
  SQLite.
- Periodically checks for in-game "ticks" and re-posts the scouting list on a
  configurable delay.

---

## Project At a Glance

| Property | Value |
|---|---|
| Language | Python 3.13 (`.python-version` pins to `3.13`) |
| Package manager | `uv` (see `pyproject.toml` and `uv.lock`); `prek` for pre-commit hooks (uv tool) |
| Runtime | `discord.py 2.6`, `aiosqlite`, `pyzmq`, `aiohttp` |
| Test framework | `unittest` (stdlib `IsolatedAsyncioTestCase`) |
| Linter/formatter | `ruff` (config in `pyproject.toml`) |
| Database | SQLite, file at `./workspace/spyplane.db` (prod) or `./tests/test_workspace/spyplane.db` (test) |
| Containerisation | Docker via `Dockerfile` + `entrypoint.sh` |
| CI | GitHub Actions — builds and pushes a Docker image on `v*` tag push (`.github/workflows/build.yml`) |
| Line length | 120 characters (configured in `pyproject.toml`) |
| Target Python | `>=3.10` (ruff `target-version = "py310"`) |

---

## Repository Layout

```
SpyPlane/
├── ptn/spyplane/            # Main source package (installable as ptn-spyplane)
│   ├── spy_plane.py         # Entry point — SpyPlane Bot class + run()
│   ├── bot_registry.py      # Singleton registry to avoid circular imports
│   ├── constants.py         # All env-driven config; prod/test switch; logging helpers
│   ├── discord_listener.py  # Discord event handlers (on_ready, reactions, etc.)
│   ├── eddn_listener.py     # Background thread for EDDN ZMQ stream
│   ├── ruff_commands.py     # Wrappers for `uv run lint / format / lint-fix`
│   ├── _metadata.py         # __version__
│   ├── commands/            # One file per slash command; __init__.py imports all
│   ├── database/            # Repository classes (base + one per table group)
│   ├── helpers/             # journal_helper.py — EDDN event filtering
│   ├── models/              # Dataclasses: ScoutSystem, Config, ScoutHistory
│   ├── services/            # Business logic: posting, tick, faction states, etc.
│   └── scripts/             # SQL export helpers
├── tests/                   # unittest test suite
│   ├── test_workspace/      # Test database lives here (spyplane.db)
│   └── test_data/           # Static fixtures
├── db/
│   ├── schema.sql           # Canonical DB schema (always kept up-to-date)
│   ├── recreate.sh          # Recreates the production workspace DB
│   ├── test_recreate.sh     # Recreates the test DB (used before running tests)
│   └── data/                # seed_database.py + compressed system CSVs
├── eddn_proxy/              # Standalone ZMQ proxy utilities (not part of main bot)
├── workspace/               # Runtime directory — gitignored DB, CSV files
├── pyproject.toml           # Project metadata, dependencies, ruff config, scripts
├── uv.lock                  # Locked dependencies (commit changes to this)
├── Dockerfile               # Docker build (python:3.13-slim-bookworm base)
├── entrypoint.sh            # Docker CMD — optionally recreates DB then runs bot
└── localrun.sh              # Docker convenience script for local runs
```

The `spyplane/` directory at the repo root contains only `__pycache__` subdirectories — it is a legacy artifact and should not be edited.

---

## Environment & Secrets

Copy `.env.sample` to `.env` and populate all values. **Never hardcode secrets.**
The bot reads credentials exclusively from environment variables via `python-dotenv`.

Key environment variables (all read in `ptn/spyplane/constants.py`):

| Variable | Purpose |
|---|---|
| `PRODUCTION` | `"True"` = prod Discord server, `"False"` (default) = test server |
| `SPYPLANE_DISCORD_TOKEN_PROD` | Discord bot token for production |
| `SPYPLANE_DISCORD_TOKEN_TESTING` | Discord bot token for test/dev |
| `APPLICATION_ID_PROD` / `APPLICATION_ID_TESTING` | Discord application IDs |
| `PROD_DISCORD_GUILD` / `TEST_DISCORD_GUILD` | Guild IDs for slash command sync |
| `EDDN_URL` | ZMQ endpoint (default: `tcp://eddn.edcd.io:9500`) |
| `EDDN_DISABLE` | Set to `"true"` to skip starting the EDDN listener thread |
| `EDDN_DUMP` | Set to `"True"` to dump raw EDDN events to `workspace/eddn_events.jsonl` |
| `DB_RECREATE` | Set to any value in Docker to trigger DB recreation on startup |

`PRODUCTION=False` is the correct setting for all local development and testing.
The `is_test` flag in `constants.py` is set automatically when `unittest` is
detected in `sys.modules` — do not set it manually.

---

## Bootstrap & Dependency Installation

Always run `uv sync` before doing anything else:

```bash
uv sync --extra dev
```

This installs all runtime + dev dependencies into `.venv` and builds the
`ptn-spyplane` package in editable mode. Run this again after any change to
`pyproject.toml` or `uv.lock`.

Install `prek` as a uv tool and set up the git pre-commit hook:

```bash
uv tool install prek
prek install
```

`prek` is a Rust-reimplementation of `pre-commit` and runs ruff lint + format
checks automatically on `git commit`. The config is in `.pre-commit-config.yaml`.

---

## Database Setup

### Test database (required before running tests)

```bash
bash db/test_recreate.sh
```

This script:
1. Deletes `tests/test_workspace/spyplane.db`
2. Creates the schema from `db/schema.sql`
3. Extracts `db/data/system_names.csv.7z` (requires `7zr` / `p7zip` to be installed)
4. Imports system names via `db/data/import.sql`

**You must run this before running tests on a fresh clone or after any schema
change.** Tests will fail with `sqlite3.OperationalError: no such table: …`
if the test DB does not exist or is stale.

### Production/dev database

```bash
bash db/recreate.sh
```

Same steps but writes to `./workspace/spyplane.db` and also seeds with
`db/data/seed_database.py`.

---

## Running Tests

```bash
bash db/test_recreate.sh          # ensure test DB is up-to-date
uv run python -m unittest discover tests -v
```

- There are **33 tests** across 8 test files.
- All 33 tests pass when the test DB is present.
- Tests that hit the database use `IsolatedAsyncioTestCase` and import `bot`
  from `ptn.spyplane.spy_plane` to open/close the real SQLite connection.
- `test_post_after_tick_service.py` makes a real HTTP request to
  `http://tick.infomancer.uk/galtick.json` — it requires network access.
- The `PyNaCl is not installed` warning printed during test runs is harmless
  (it only affects Discord voice features).

---

## Linting & Formatting

```bash
uv run lint          # ruff check . (all directories)
uv run format        # ruff format . (auto-fix formatting)
uv run lint-fix      # ruff check --fix . (auto-fix lint issues)
```

Run pre-commit checks on all files manually with:

```bash
prek run --all-files
```

**Important**: `prek run --all-files` may modify files on first run (fixing
trailing whitespace, missing final newlines, etc.) and exit non-zero. Run it a
second time to confirm all hooks pass cleanly.

The ruff config (in `pyproject.toml`) uses a broad rule set including: `E/W`
(pycodestyle), `F` (pyflakes), `I` (isort), `PL` (pylint), `RUF` (ruff), `B`
(bugbear), `S` (bandit/security), `UP` (pyupgrade), `SIM` (simplify), `TC`
(type-checking), `PERF` (perflint), `FURB` (refurb), and others. `E501`
(line-too-long) is ignored — line length is handled by the formatter at 120
characters. `PLR` (pylint-refactor) is also ignored.

**Formatting is clean** — `ruff format --check .` reports no files to
reformat. Always run `uv run format` on any files you touch.

**Linting is clean** — `uv run lint` reports `All checks passed!`. Do not
introduce new violations.

Linting and formatting are enforced locally via **`prek`** (installed as a uv
tool). They are **not enforced in CI** — the GitHub Actions workflow only
builds and pushes a Docker image.

To check only the main source tree:

```bash
uv run ruff check ptn/
uv run ruff check tests/
```

---

## CI / GitHub Actions

The only CI pipeline is `.github/workflows/build.yml`. It:
- Triggers on **`v*` tag pushes** and manual `workflow_dispatch`.
- Logs in to the PTN container registry, builds the Docker image passing the
  tag version as `--build-arg VERSION=<tag>`, and pushes it.
- Tags the image with the full tag name (e.g. `v1.2.3`). On clean semver tags,
  also updates the `latest` tag.
- **Does not run tests, linting, or type-checking.**

To build the Docker image locally with the correct SCM version baked in:

```bash
docker build --build-arg VERSION=$(uvx --from setuptools-scm python -m setuptools_scm) -t spyplane .
```

---

## Critical Import Order & Circular Import Rules

The codebase has carefully managed import ordering to prevent circular imports.
Follow these rules exactly when adding new code:

1. **`bot_registry.py`** is the single source of truth for the bot instance.
   It uses `TYPE_CHECKING` guards so `SpyPlane` is never imported at runtime
   from within it. All modules that need the bot call `get_bot()` at call-time,
   not at import time.

2. **`spy_plane.py` `run()` function**: `Commands` and `DiscordListener` are
   imported **inside** `run()`, not at module top level. This is intentional
   and must be preserved. Do not move these imports to the top of the file.

3. **`commands/__init__.py`**: Imports all command modules for side-effect
   registration, and declares `__all__` to explicitly re-export them. Add new
   command modules to both the import block and `__all__` when creating a new
   command.

4. **`database/base_repository.py`**: Imports `get_bot` inside methods, not
   at module level, to avoid circular imports at startup.

5. **`eddn_listener.py`**: The `EddnListenerThread` singleton is created
   lazily via `get_eddn_listener_thread()`. Do not instantiate
   `EddnListenerThread` directly anywhere else.

6. Module dependency direction (no cycles allowed):
   ```
   commands/  →  services/  →  database/  →  models/
   discord_listener  →  services/
   eddn_listener  →  services/ + helpers/
   All of the above  →  bot_registry + constants
   ```

---

## Adding a New Slash Command

1. Create `ptn/spyplane/commands/my_command.py` following the pattern of
   existing command files (use `@bot.tree.command` or `@app_commands`).
2. Add `from ptn.spyplane.commands import my_command` to
   `ptn/spyplane/commands/__init__.py`.
3. No further registration is needed — `Commands()` in `run()` triggers the
   import.

---

## Versioning

Version is managed via **`setuptools_scm`** — it is derived automatically from
the git tag at build time. There is **no hardcoded version** in the source.

- `pyproject.toml` declares `dynamic = ["version"]` and configures
  `[tool.setuptools_scm]` with `fallback_version = "0.0.0+unknown"`.
- `ptn/spyplane/_metadata.py` reads the version at runtime via
  `importlib.metadata.version("ptn-spyplane")`.
- During Docker builds, the CI workflow passes `--build-arg VERSION=<tag>`
  and the Dockerfile sets `SETUPTOOLS_SCM_PRETEND_VERSION` so the version is
  baked into the installed dist-info without needing `.git` in the image.
- When running locally from a git clone, `uv sync` resolves the version from
  git tags automatically. If no tags are present, `0.0.0+unknown` is used.

**Summary of what to run before submitting:**
1. `uv sync --extra dev`
2. `prek run --all-files` — run twice if first run exits non-zero due to auto-fixes
3. `uv run python -m unittest discover tests -v` — must pass with all 33 tests `OK`

## Key Files Quick Reference

| File | Purpose |
|---|---|
| `ptn/spyplane/_metadata.py` | `__version__` via `importlib.metadata` (SCM-derived) |
| `ptn/spyplane/constants.py` | All config, channel/role IDs, env vars, logging |
| `ptn/spyplane/spy_plane.py` | Bot class (`SpyPlane`), DB lifecycle, entry point `run()` |
| `ptn/spyplane/bot_registry.py` | `register_bot()` / `get_bot()` singleton |
| `ptn/spyplane/discord_listener.py` | `on_ready`, `on_message`, `on_raw_reaction_add`, error handler |
| `ptn/spyplane/eddn_listener.py` | ZMQ background thread, EDDN event processing |
| `ptn/spyplane/database/base_repository.py` | Base class with `db()`, `begin()`, `commit()`, `rollback()` |
| `ptn/spyplane/database/systems_repository.py` | `scout_systems` + `scout_systems_posted` table operations |
| `ptn/spyplane/services/systems_posting_service.py` | Post scouting list to Discord channel |
| `ptn/spyplane/services/tick_service.py` | Poll tick API, detect new ticks |
| `ptn/spyplane/services/post_after_tick_service.py` | Schedule system posting after tick |
| `ptn/spyplane/services/faction_state_service.py` | Extract + persist faction states from EDDN |
| `ptn/spyplane/helpers/journal_helper.py` | Filter EDDN events by type + tracked systems |
| `db/schema.sql` | Authoritative SQLite schema |
| `pyproject.toml` | Dependencies, ruff config, `uv` scripts, `setuptools_scm` config |
| `.pre-commit-config.yaml` | `prek`/`pre-commit` hook config (ruff check + format, file hygiene) |
