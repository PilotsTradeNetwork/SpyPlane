# Faction Tracking Commands

## Overview

The `/faction` command group manages which star systems are scouted, posts them to the scout channel, and produces
reports. Systems have one of three priorities (Primary, Secondary, Tertiary). The full list is managed through one
modal (`/faction track`) that replaces the whole list on submit.

Scouting is detected automatically from the EDDN stream. Pilots react to a posted system with the bullseye emoji to
claim credit; the scout is recorded when EDDN reports a visit to that system.

| Command | Purpose | Response visibility |
|---|---|---|
| `/faction track` | Edit the full tracked systems list (modal) | Public (errors ephemeral) |
| `/faction list` | Export tracked systems as CSV | Public |
| `/faction launch` | Post the scouting list to the scout channel now | Ephemeral |
| `/faction config name value` | Change a config value | Public |
| `/faction config_dump` | Show all config values | Public |
| `/faction refresh_progress` | Force-refresh the scouting progress embeds | Ephemeral |
| `/faction daily_report` | Post the faction state report in the current channel | Ephemeral confirmation |
| `/faction operations_report` | Top scouts of the last 90 days + full history CSV | Public |
| `@SpyPlane ping` | Reply with a gif and the bot version (text command) | Public |

Permissions are not enforced in code; restrict who can use the commands via Discord's server integration settings.

## Database Structure

### `scout_systems`
- **`system_name`** (TEXT PRIMARY KEY): Tracked system.
- **`priority`** (TEXT NOT NULL): `Primary`, `Secondary` or `Tertiary`.
- **`added_by`** (TEXT NOT NULL): Discord username of the last `/faction track` submitter.
- **`added_at`** (INTEGER NOT NULL): Unix timestamp of that submission.

### `systems`
- **`name`** (TEXT PRIMARY KEY): Known Elite Dangerous system names, imported from `db/data/system_names.csv.7z`.

### `scout_systems_posted`
Systems posted by the latest launch. Cleared on every launch.
- **`system_name`** (TEXT PRIMARY KEY)
- **`priority`** (TEXT NOT NULL)
- **`message_id`** (INTEGER): Discord message of the posted system.
- **`scouted`** (INTEGER, default 0): Set to 1 when scouted (soft-delete), so per-tick counts stay accurate.

### `scout_history`
One row per recorded scout: `id`, `system_name`, `username`, `userid`, `timestamp`. `username` is `EDDN` and
`userid` is `0` when nobody claimed the system.

### `faction_states`
Latest faction data per `(system, faction)` from EDDN: `active_csv`, `pending_csv`, `influence`, `controlling`.

### `configuration`

| Name | Default | Settable via `/faction config` | Meaning |
|---|---|---|---|
| `interval_hours` | 4 | Yes (1-24) | Hours after a tick before the scouting list is posted |
| `daily_interval_hours` | 12 | No | Hours after a tick before the daily report is posted |
| `primary_limit` | 0 | Yes (>= 0) | Max Primary systems per post, 0 = no limit |
| `secondary_limit` | 0 | Yes (>= 0) | Max Secondary systems per post, 0 = no limit |
| `tertiary_limit` | 0 | Yes (>= 0) | Max Tertiary systems per post, 0 = no limit |
| `selection_mode` | `oldest_first` | Yes (`oldest_first`, `absolute`) | Ordering before limits apply (see `/faction launch`) |
| `tracked_changed_at` | 0 | No | Set by `/faction track`; start of the "totals" window |
| `last_posted_at` | 0 | No | Set by each launch; scout deduplication boundary |
| `faction_goals_message_id` | - | No | Goals embed message (see [Faction Goals](FACTION_GOALS.md)) |

## Commands

### `/faction track`
Opens a modal with the current list prefilled. The submitted list **replaces the entire tracking list**.

**Modal fields** (all optional, one system per line, max 1000 characters each):
- **Primary Systems**
- **Secondary Systems**
- **Tertiary Systems**

An empty field clears that priority. Duplicate names are saved once (first occurrence wins).

**Validation:**
1. Each name is checked against the local `systems` table (exact, case-sensitive match)
2. Names not found locally are looked up in one bulk request to EDSM (case-insensitive)
3. If any name is found in neither, the whole submission is rejected:
   ```
   ## Errors
   System(s) not found: InvalidSystem, Typo System
   ```
4. For names resolved via EDSM, non-blocking warnings are shown for:
   - Non-Tertiary systems more than 500 ly from Sol
   - Systems EDSM reports as possibly unpopulated

If EDSM is unreachable, every name missing from the local table is reported as not found.

**On success:**
- `scout_systems` is replaced in one transaction and the in-memory cache (used by the EDDN listener) is reloaded
- `added_by` / `added_at` are set to the submitter and the current time for **every** system
- `tracked_changed_at` is set to now, which resets the "Scouting Totals" embed window
- The scout channel is **not** reposted; run `/faction launch` or wait for the next tick

**Example response:**
```
✅ Saved 8 tracked system(s):
- 3 Primary
- 3 Secondary
- 2 Tertiary

⚠️ Distant Systems not in Tertiary List: Far System (Primary)
⚠️ Possibly not populated: Empty System
```

---

### `/faction list`
Exports all tracked systems as a CSV attachment.

- Columns: System Name, Priority, Added By, Added At (`YYYY-MM-DD HH:MM:SS`, UTC)
- File name: `tracked_systems_YYYYMMDD_HHMMSS.csv`
- Embed with the total and per-priority counts:
  ```
  📋 Tracked Systems Export
  Exported 25 tracked systems to CSV file
  🎯 Primary: 10   ⚡ Secondary: 8   📊 Tertiary: 7
  ```
- With no tracked systems: `📋 No systems are currently being tracked`

---

### `/faction launch`
Posts the scouting list to the scout channel immediately. The same routine runs automatically after each tick (see
[Automatic Posting](#automatic-posting-after-tick)).

**Behavior:**
1. Clears `scout_systems_posted`
2. Deletes all non-pinned messages in the scout channel
3. Sets `last_posted_at` to now
4. Selects systems per priority:
   - **Primary**: always included
   - **Secondary**: skipped if scouted in the last 24 hours
   - **Tertiary**: skipped if scouted in the last 48 hours
   - Sorted by `selection_mode`, then cut to the per-priority limit
5. Posts each system as its own message with a bullseye reaction, Primary first, then `__**Secondary List**__` and
   `__**Tertiary List**__` headers
6. Stores each message ID in `scout_systems_posted`
7. If any systems are tracked, pings the Faction Scout role:
   ```
   @Faction Scout List Updated
   Link to top: <jump URL to first Primary message>
   ```

**Selection modes:**
- `oldest_first` (default): Least recently scouted first, using each system's latest `scout_history` entry. Systems
  never scouted come first. Ties are broken by `added_at`. With a limit set, scouted systems move to the back, so the
  posted list rotates through all systems over successive postings.
- `absolute`: Order as stored in the database, ignoring scout history.

**Response:** `Spy plane is now on the prowl!` (ephemeral)

---

### `/faction config`
Sets a config value.

**Parameters:**
- **`name`** (choice): `interval_hours`, `primary_limit`, `secondary_limit`, `tertiary_limit`, `selection_mode`
- **`value`**: New value. Autocompletes for `selection_mode`. Values are lower-cased.

**Validation:**
- `interval_hours`: integer 1-24
- `*_limit`: non-negative integer, `0` = no limit
- `selection_mode`: `oldest_first` or `absolute`

**Examples:**
```
/faction config name:secondary_limit value:10
→ Config secondary_limit was set to 10

/faction config name:interval_hours value:30
→ Config was not set. interval_hours supports only numbers between 1 and 24
```

---

### `/faction config_dump`
Shows every row of the `configuration` table in an embed, including values not settable via `/faction config`.

---

### `/faction refresh_progress`
Immediately refreshes both scouting progress embeds (see [Scouting Progress Embeds](#scouting-progress-embeds)).
If the background refresh task has stopped, it is restarted and the response says so:
```
✅ Scouting progress embed refreshed.
⚠️ The progress service was not running and has been restarted.
```

---

### `/faction daily_report`
Posts the faction state report in the channel where the command is run. The automatic post after each tick goes to
the monitoring channel instead.

**Content:**
- **PTN Expansion** field: every system in `faction_states` where Pilots Trade Network influence is above 65%
  (`warning`) or 70% (`danger`), tracked or not. Format: `Kambarci - danger (72.5%)`
- One field per **tracked** system that has at least one non-expansion state:
  `Faction Name - war (Active)` / `Faction Name - election (Pending)`. State names are lower-case; expansion is
  omitted.
- Embed footer: "P.T.N. Faction News ™" with the GalNet icon, timestamped now

**Example:**
```
PTN Expansion
Kambarci - danger (72.5%)
LHS 3447 - warning (67.2%)

Kambarci
Pilots Trade Network - war (Active)
Local Faction - civilwar (Pending)
```

Data comes from EDDN; systems nobody has visited since tracking started have no states.

---

### `/faction operations_report`
Classified scout activity report.

**Behavior:**
1. Reads `scout_history` and keeps entries from the last 90 days
2. Ranks usernames by scout count; shows the top 5 with 🥇🥈🥉🏅
3. Exports the **full** `scout_history` table to `./workspace/faction_command_eyesonly.csv` and attaches it

**Responses:**
- **Success**: Green embed `🔍 Faction Operations Report` with total activity, top 5, footer
  `[TOP SECRET] Eyes-Only Faction Command`, plus CSV
- **No activity**: Red embed, `No scout activity recorded in the last 3 months. Asset status: INACTIVE`
- **CSV failure**: Embed plus `⚠️ CSV export failed, but scout rankings are available above.`
- **Error**: Red embed, `Asset compromised. Report failed. Escalate to flight command.`

EDDN-attributed scouts are ranked under the username `EDDN`.

**CSV format:**
```csv
id,system_name,username,userid,timestamp
1,Kambarci,PilotName,123456789,1704067200.0
2,LHS 3447,EDDN,0,1704070800.0
```

---

### `@SpyPlane ping`
Text command (prefix is a bot mention or `🕵`). Replies with a random gif and the bot version. Mentioning the bot
without a command replies with a greeting gif.

---

## Automatic Posting After Tick

`PostAfterTickService` polls `http://tick.infomancer.uk/galtick.json` every 5 minutes. On a new galaxy tick it:
1. Posts `Tick detected. Spy Plane will take off in ~ N hours` in the scout channel
2. After `interval_hours`, runs the same routine as `/faction launch`
3. After `daily_interval_hours`, posts the daily report to the monitoring channel

The wait is in memory; a bot restart during the wait cancels that post.

## EDDN Listener: Automated Scouting

The listener runs in a background thread and subscribes to the EDDN ZMQ stream (`EDDN_URL`, default
`tcp://eddn.edcd.io:9500`).

### How it works
1. Only `FSDJump`, `Location` and `CarrierJump` events for systems in the tracked cache are processed
2. For a matching event:
   - If the system has a posted message, the first non-bot user who reacted with the bullseye gets credit;
     otherwise the scout is attributed to `EDDN` (userid `0`). Multiple reactors are logged; the first wins.
   - A scout row is written to `scout_history` and `scout_systems_posted.scouted` is set to 1, unless the system
     was already scouted since `last_posted_at` (one scout per system per posting)
   - The system's message is deleted from the scout channel (unless pinned)
   - Faction states for the system are replaced with the event's faction data

### Configuration
- `EDDN_DISABLE=true` (case-insensitive): do not start the listener
- `EDDN_DUMP=True` (exact): append every received event to `./workspace/eddn_events.jsonl`
- `EDDN_URL`: ZMQ endpoint, e.g. `ipc:///tmp/eddn` when using a local proxy

### Example flow
1. Admin adds Kambarci as Primary via `/faction track`, then runs `/faction launch`
2. A pilot reacts to the Kambarci message with the bullseye and jumps there with EDMC running
3. EDDN delivers the FSDJump; the listener records the scout for that pilot, deletes the message and updates
   faction states
4. Later visits before the next posting update faction states but do not add more scout rows

### Limitations
- Only visits by players running EDDN-enabled tools (EDMC, EDDiscovery, etc.) are detected
- Reacting alone does not record a scout
- Only systems in the tracked cache are processed

## Scouting Progress Embeds

`ScoutingProgressService` refreshes two embeds every 10 minutes (or on `/faction refresh_progress`):

| Embed | Channel | Counts |
|---|---|---|
| `📡 Scouting Progress (This Tick)` | Scout channel | Scouted / posted per priority from `scout_systems_posted` |
| `📊 Scouting Totals (Since Last Change)` | Monitoring channel | Unique tracked systems scouted since `tracked_changed_at` / tracked per priority |

- Each line reads `scouted/total (pct%)`; priorities with no systems are hidden
- Color: green when all priorities are 100%, yellow when any is at least 50%, red otherwise, grey when empty
- The bot edits its last message; after a restart it finds the embed among the channel's **pinned** messages by
  title, otherwise it posts a new one
- `/faction launch` deletes non-pinned messages in the scout channel, so **pin the progress embed** to keep a
  single message

## Channel and Role Configuration

All IDs live in `ptn/spyplane/constants.py` and switch on `PRODUCTION`:

| Purpose | Prod constant | Test constant |
|---|---|---|
| Scout channel (list, progress embed) | `PROD_CHANNEL_SCOUT` | `TEST_CHANNEL_SCOUT` |
| Monitoring channel (daily report, totals embed) | `PROD_CHANNEL_MONITORING` | `TEST_CHANNEL_MONITORING` |
| Bot dev channel (startup message) | `PROD_BOT_DEV_CHANNEL` | `TEST_BOT_DEV_CHANNEL` |
| Faction Scout role (launch ping) | `PROD_ROLE_SCOUT` | `TEST_ROLE_SCOUT` |
| Bullseye reaction emoji | `PROD_EMOJI_TARGET` | `TEST_EMOJI_TARGET` |

If the bullseye emoji is not available, `✅` is used.

## Best Practices

1. **System names**: Use exact in-game names; the local lookup is case-sensitive.
2. **Priorities**: Primary for daily attention, Secondary for every-other-day, Tertiary for long-term monitoring.
3. **After editing**: Run `/faction launch` if the change should be visible before the next tick.
4. **Limits**: Use `*_limit` to cap how many systems appear per priority. With `oldest_first`, systems not visited
   for longest are posted first, so a capped list still cycles through every system.
5. **Pin embeds**: Pin both progress embeds so they survive purges and restarts.

## Troubleshooting

**Q: System not found when saving?**
- Check spelling and spacing; it must exist locally or in EDSM

**Q: Systems missing after launch?**
- Check `/faction list`
- Secondary/Tertiary systems scouted in the last 24h/48h are skipped
- Check limits with `/faction config_dump`

**Q: Systems not auto-scouted?**
- The visiting player must run an EDDN-enabled tool
- Check logs for `EDDN listener started` and `Connected to EDDN stream`, and that `EDDN_DISABLE` is not set
- Only one scout per system is recorded per posting

**Q: Wrong pilot credited?**
- Credit goes to the first non-bot user who reacted before the EDDN visit; no reaction means `EDDN`

**Q: Progress embed reposted on every launch?**
- Pin it in the scout channel

**Q: Channel not purged?**
- Pinned messages are never deleted; check bot permissions in the scout channel
