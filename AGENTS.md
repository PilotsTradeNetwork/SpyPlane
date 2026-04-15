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
| Package manager | `uv` (see `pyproject.toml` and `uv.lock`) |
| Runtime | `discord.py 2.6`, `aiosqlite`, `pyzmq`, `aiohttp`, `ptn-utils 1.1.1` |
| Test framework | `unittest` (stdlib `IsolatedAsyncioTestCase`) |
| Linter/formatter | `ruff` (config in `pyproject.toml`) |
| Database | SQLite, file at `./ptn/data/spyplane.db` (prod) or `./tests/test_workspace/spyplane.db` (test) |
| Containerisation | Docker via `Dockerfile` + `entrypoint.sh` |
| CI | GitHub Actions — builds and pushes a Docker image on tag push (`.github/workflows/build.yml`) |
| Line length | 120 characters (configured in `pyproject.toml`) |
| Target Python | `>=3.10` (ruff `target-version = "py310"`) |

---

## Repository Layout

```
SpyPlane/
├── ptn/
│   ├── __init__.py
│   ├── data/                # Runtime data directory — DB, CSV exports, .env, EDDN dump
│   │   └── .env             # Discord tokens + secrets (not committed; copy from .env.sample)
│   └── spyplane/            # Main source package (installable as ptn-spyplane)
│       ├── spy_plane.py     # Entry point — SpyPlane Bot class + run()
│       ├── bot_registry.py  # Singleton registry to avoid circular imports
│       ├── constants.py     # SpyPlane-specific constants; logging wrappers
│       ├── discord_listener.py  # Discord event handlers (on_ready, reactions, etc.)
│       ├── eddn_listener.py     # Background thread for EDDN ZMQ stream
│       ├── ruff_commands.py     # Wrappers for `uv run lint / format / lint-fix`
│       ├── _metadata.py         # __version__
│       ├── commands/            # One file per slash command; __init__.py imports all
│       ├── database/            # Repository classes (base + one per table group)
│       ├── helpers/             # journal_helper.py — EDDN event filtering
│       ├── models/              # Dataclasses: ScoutSystem, Config, ScoutHistory
│       ├── services/            # Business logic: posting, tick, faction states, etc.
│       └── scripts/             # SQL export helpers
├── tests/                   # unittest test suite
│   ├── test_workspace/      # Test database lives here (spyplane.db)
│   └── test_data/           # Static fixtures
├── db/
│   ├── schema.sql           # Canonical DB schema (always kept up-to-date)
│   ├── recreate.sh          # Recreates the production ptn/data DB
│   ├── test_recreate.sh     # Recreates the test DB (used before running tests)
│   └── data/                # seed_database.py + compressed system CSVs
├── eddn_proxy/              # Standalone ZMQ proxy utilities (not part of main bot)
├── pyproject.toml           # Project metadata, dependencies, ruff config, scripts
├── uv.lock                  # Locked dependencies (commit changes to this)
├── requirements.lock        # pip-compatible lock used by Docker image
├── Dockerfile               # Docker build (python:3.10-slim-bookworm base)
├── entrypoint.sh            # Docker CMD — optionally recreates DB then runs bot
└── localrun.sh              # Docker convenience script for local runs
```

---

## Environment & Secrets

Place a `.env` file at `ptn/data/.env` (this is the `DATA_DIR` location that PTN-Library reads
automatically). **Never hardcode secrets and never commit `.env`.**

Key environment variables:

| Variable | Where read | Purpose |
|---|---|---|
| `PTN_SERVICE` | `ptn_utils.global_constants` | `"True"` = prod Discord server, `"False"` (default) = test server |
| `DISCORD_TOKEN_PROD` | `ptn/data/.env` via `ptn_utils` | Discord bot token for production |
| `DISCORD_TOKEN_TESTING` | `ptn/data/.env` via `ptn_utils` | Discord bot token for test/dev |
| `EDDN_URL` | `ptn/spyplane/constants.py` | ZMQ endpoint (default: `tcp://eddn.edcd.io:9500`) |
| `EDDN_DISABLE` | `ptn/spyplane/discord_listener.py` | Set to `"true"` to skip starting the EDDN listener thread |
| `EDDN_DUMP` | `ptn/spyplane/eddn_listener.py` | Set to `"True"` to dump raw EDDN events to `ptn/data/eddn_events.jsonl` |
| `DB_RECREATE` | `entrypoint.sh` | Set to any value in Docker to trigger DB recreation on startup |
| `PTN_LOG_LEVEL` | `ptn_utils.logger` | Initial log level: `CRITICAL`, `ERROR`, `WARNING`, `INFO` (default), `DEBUG`, `TRACE` |

`PTN_SERVICE=False` (or unset) is the correct setting for all local development and testing.
The `is_test` flag in `constants.py` is set automatically when `unittest` is
detected in `sys.modules` — do not set it manually.

### Token & Guild IDs

PTN-Library provides `TOKEN`, `DISCORD_GUILD`, and `guild_obj` from `ptn_utils.global_constants`
(selected via `PTN_SERVICE`). SpyPlane reads these directly — no separate token env vars are needed
beyond what PTN-Library loads from `ptn/data/.env`.

---

## Bootstrap & Dependency Installation

Always run `uv sync` (with `--extra dev` for linting tools) before doing
anything else:

```bash
uv sync --extra dev
```

This installs all runtime + dev dependencies into `.venv` and builds the
`ptn-spyplane` package in editable mode. Run this again after any change to
`pyproject.toml` or `uv.lock`.

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

Same steps but writes to `./ptn/data/spyplane.db` and also seeds with
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
- Before running tests, ensure `ptn/data/.env` exists (even if empty) so PTN-Library's
  `load_dotenv` does not raise on import.
- The `PyNaCl is not installed` warning printed during test runs is harmless
  (it only affects Discord voice features).

---

## Linting & Formatting

```bash
uv run lint          # ruff check . (all directories)
uv run format        # ruff format . (auto-fix formatting)
uv run lint-fix      # ruff check --fix . (auto-fix lint issues)
```

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

Linting and formatting are **not enforced in CI** — the GitHub Actions workflow
only builds and pushes a Docker image. However, keep new code clean.

To check only the main source tree:

```bash
uv run ruff check ptn/
uv run ruff check tests/
```

---

## CI / GitHub Actions

The only CI pipeline is `.github/workflows/build.yml`. It:
- Triggers on **tag pushes** (any tag) and manual `workflow_dispatch`.
- Logs in to the PTN container registry, builds the Docker image, and pushes
  it tagged with both a timestamp and `latest`.
- **Does not run tests, linting, or type-checking.**

There are no pre-commit hooks configured in this repository.

To manually replicate the Docker build locally:

```bash
bash localrun.sh
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

## Key Files Quick Reference

| File | Purpose |
|---|---|
| `ptn/spyplane/constants.py` | SpyPlane-specific channel/role/emoji IDs; `DB_PATH`; `EDDN_URL`; loguru `log`/`log_exception` wrappers |
| `ptn/data/.env` | Discord tokens (`DISCORD_TOKEN_PROD`, `DISCORD_TOKEN_TESTING`) loaded by PTN-Library |
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

### PTN-Library constants used by SpyPlane

Import from `ptn_utils.global_constants`:

| Symbol | Description |
|---|---|
| `TOKEN` | Active Discord bot token (selected by `PTN_SERVICE`) |
| `DISCORD_GUILD` | Guild ID for the active environment |
| `guild_obj` | `discord.Object(DISCORD_GUILD)` |
| `CHANNEL_BOTSPAM` | Bot spam channel |
| `CHANNEL_DEV_SPY_PLANE` | SpyPlane dev/bot channel (replaces `BOT_DEV_CHANNEL`) |
| `ROLE_COUNCIL` | Council role |
| `ROLE_MOD` | Mod role |
| `ROLE_FO` | Faction Operative role (replaces `ROLE_OPERATIVE`) |
| `EMOJI_ASSASSIN` | Assassin emoji (replaces `EMOJI_TARGET`) |
| `any_moderation_role` | `[ROLE_COUNCIL, ROLE_MOD]` |
| `pyproject.toml` | Dependencies, ruff config, `uv` scripts |
