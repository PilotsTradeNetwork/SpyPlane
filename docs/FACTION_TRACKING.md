# Faction Tracking Commands Documentation

## Overview

The Faction Tracking system allows administrators to manage which star systems are being monitored for faction scouting operations. Systems are organised into three priority levels (Primary, Secondary, Tertiary) and posted to the scout channel for pilots to visit. The full tracking list is managed through a single modal interface (`/faction track`), which replaces the entire list each time it is submitted. The system validates system names against the local Elite Dangerous database and optionally cross-checks unknown names with EDSM.

## Database Structure

### `scout_systems` Table
- **`system_name`** (TEXT PRIMARY KEY): The star system name being tracked. Must be unique.
- **`priority`** (TEXT NOT NULL): Priority level - one of "Primary", "Secondary", or "Tertiary".
- **`added_by`** (TEXT NOT NULL): Discord username of the person who added the system.
- **`added_at`** (INTEGER NOT NULL): Unix timestamp when the system was added.

### `systems` Table
- **`name`** (TEXT PRIMARY KEY): Valid star system names from Elite Dangerous. Used for validation.

### `scout_systems_posted` Table
- **`system_name`** (TEXT PRIMARY KEY): System that has been posted to the scout channel.
- **`priority`** (TEXT NOT NULL): Priority level of the posted system.
- **`message_id`** (INTEGER): Discord message ID of the posted system message.

## Commands

### `/faction track`
Sets the full list of systems to track for faction scouting. Opens a modal with three text fields (one per priority level). The submitted list **replaces the entire current tracking list**.

**Modal Fields:**
- **Primary Systems**: One system name per line
- **Secondary Systems**: One system name per line
- **Tertiary Systems**: One system name per line

All fields are optional. Leaving a field empty clears all systems of that priority. The modal is pre-populated with the current tracked systems so you can edit in-place.

**Validation:**
- System names are first checked against the local `systems` table
- Names not found locally are bulk-fetched from EDSM as a fallback
- Any name not found in either source causes the entire submission to be rejected with the unknown names listed
- Warnings (non-blocking) are shown for:
  - Non-Tertiary systems more than 500 ly from the bubble
  - Systems that may not be populated

**Behavior:**
- On successful submission the entire `scout_systems` table is replaced atomically
- `added_by` is set to the submitting user's Discord username
- `added_at` is set to the current Unix timestamp for each system
- The `tracked_changed_at` config value is updated to the current time

**Example response:**
```
✅ Saved 8 tracked system(s):
- 3 Primary
- 3 Secondary
- 2 Tertiary
```

**To remove systems:** re-open the modal, delete the unwanted lines, and resubmit.

**To clear a priority entirely:** leave that field blank and resubmit.

**Error case:**
```
## Errors
System(s) not found: InvalidSystem, Typo System
```

---

### `/faction list`
Exports all currently tracked systems to a CSV file.

**Parameters:**
- None

**Output:**
- Creates a CSV file with columns:
  - **System Name**: The star system name
  - **Priority**: Priority level (Primary/Secondary/Tertiary)
  - **Added By**: Discord username who added the system
  - **Added At**: Timestamp when the system was added (YYYY-MM-DD HH:MM:SS format)
- Sends the file as a Discord attachment
- Includes an embed with:
  - Total count of tracked systems
  - Breakdown by priority (Primary, Secondary, Tertiary counts)

**File Naming:**
- Format: `tracked_systems_YYYYMMDD_HHMMSS.csv`
- Example: `tracked_systems_20240115_143022.csv`

**Example Output:**
```
📋 Tracked Systems Export
Exported 25 tracked systems to CSV file

🎯 Primary: 10
⚡ Secondary: 8
📊 Tertiary: 7
```

**No Systems Tracked:**
```
/faction list
→ 📋 No systems are currently being tracked
```

---

### `/faction launch`
Posts all tracked systems to the scout channel, organized by priority.

**Parameters:**
- None

**Behavior:**
1. **Fetches tracked systems** from the database
2. **Purges the scout channel** - deletes all non-pinned messages
3. **Filters recently scouted systems**:
   - Secondary systems scouted within the last 1 day are hidden
   - Tertiary systems scouted within the last 2 days are hidden
   - Primary systems are always shown
4. **Sorts and limits** by priority using the configured `selection_mode` and per-priority limits
5. **Posts systems** to the scout channel:
   - Each system posted as a separate message
   - Each message gets a reaction emoji (bullseye/target)
   - Systems grouped by priority with headers
6. **Stores message IDs** in `scout_systems_posted` table for tracking
7. **Sends notification** to the Faction Scout role with link to first message

**Selection Modes (`selection_mode` config):**
- `oldest_first`: Systems with the earliest `added_at` timestamp are posted first; systems with `added_at = 0` sort last
- `absolute`: Systems are posted in insertion order as returned from the database

**Per-priority Limits:**
- `primary_limit`, `secondary_limit`, `tertiary_limit` cap how many systems are posted per priority
- A limit of `0` means no cap - all eligible systems are posted

**Channel Format:**
```
[Primary systems - no header]
System1
System2
System3

__**Secondary List**__
System4
System5

__**Tertiary List**__
System6
System7
```

**Response:**
```
Spy plane is now on the prowl!
```

**Notification:**
After posting, sends a message to the scout channel:
```
<@&FACTION_SCOUT_ROLE_ID> List Updated
Link to top: [jump URL to first message]
```

**Important Notes:**
- Command is ephemeral (only visible to the executor)
- All non-pinned messages in the scout channel are deleted before posting
- Message IDs are stored for future reference
- Systems are posted in the order they appear in the database

---

## EDDN Listener - Automated Scouting

The EDDN (Elite Dangerous Data Network) listener provides automated scouting capabilities for tracked systems. When enabled, it monitors the EDDN stream for player activity in tracked systems and automatically marks them as scouted.

### How It Works

1. **EDDN Stream Monitoring**: The bot connects to the EDDN stream (default: `tcp://eddn.edcd.io:9500`) via ZMQ and receives real-time player journal events from Elite Dangerous.

2. **Event Filtering**: The listener only processes specific event types from tracked systems:
   - **FSDJump**: When a player jumps to a system
   - **Location**: When a player's location is updated
   - **CarrierJump**: When a fleet carrier jumps to a system

3. **System Matching**: Before processing, the listener checks if the system in the event is in the tracked systems cache. Only events from tracked systems are processed.

4. **Automated Actions**: When a tracked system is detected:
   - **Records the scout**: Marks the system as scouted in the database with username "EDDN" and userid 0
   - **Deletes Discord message**: Automatically removes the system's message from the scout channel (if it exists and isn't pinned)
   - **Updates faction states**: Extracts and stores faction state information (influence, active/pending states) from the event data

### Configuration

**Enable/Disable:**
- The EDDN listener starts automatically when the bot starts (unless disabled)
- To disable: Set environment variable `EDDN_DISABLE=True`
- When disabled, the listener thread will not start

**Event Dumping:**
- Optional: Set environment variable `EDDN_DUMP=True` to save all EDDN events to a file
- Events are saved to: `./workspace/eddn_events.jsonl`
- Useful for debugging or analysis

### Benefits

1. **Automatic Scouting**: Systems are automatically marked as scouted when any player (with EDDN enabled) visits them, without requiring manual reaction clicks.

2. **Real-time Updates**: Faction state information is updated immediately when players visit tracked systems, providing current data for BGS operations.

3. **Reduced Manual Work**: Scout channel messages are automatically cleaned up when systems are scouted via EDDN.

4. **Broader Coverage**: Works for any player using EDDN-enabled tools (EDMC, EDDiscovery, etc.), not just Discord users.

### How It Integrates with Tracking

1. **Cache Synchronization**: When systems are added/removed via `/faction_track` or `/faction_remove`, the tracked systems cache is updated, which the EDDN listener uses for filtering.

2. **Message Management**: When EDDN detects a visit to a tracked system:
   - The system is removed from `scout_systems_posted` table
   - The Discord message is deleted (if not pinned)
   - Scout history is recorded

3. **Faction State Updates**: EDDN events contain faction data that is stored in the `faction_states` table, providing up-to-date information about faction influence and states.

### Limitations

- **EDDN Dependency**: Only works for players who have EDDN-enabled tools (EDMC, EDDiscovery, etc.)
- **Event Types**: Only processes FSDJump, Location, and CarrierJump events
- **System Validation**: System must be in the tracked systems cache to be processed
- **Message Deletion**: Only deletes messages that exist in `scout_systems_posted` table

### Example Flow

1. Admin adds system: `/faction_track system_names:"Kambarci" priority:Primary`
2. Admin launches list: `/faction_launch` → System posted to scout channel
3. Player with EDMC visits Kambarci → EDMC sends FSDJump event to EDDN
4. EDDN listener receives event → Checks if Kambarci is tracked → Yes
5. Listener processes event:
   - Records scout: "EDDN scouted Kambarci"
   - Deletes Discord message for Kambarci
   - Updates faction states from event data
6. System is now marked as scouted and removed from active list

### Troubleshooting EDDN Listener

**Q: EDDN listener not processing events?**
- Check if listener is enabled: Look for "EDDN listener started" in logs
- Verify `EDDN_DISABLE` is not set to "True"
- Check EDDN connection: Look for "Connected to EDDN stream" in logs

**Q: Systems not being auto-scouted?**
- Verify system is in tracked systems (use `/faction_list`)
- Check if players visiting the system have EDDN-enabled tools
- Verify the event type is one of: FSDJump, Location, CarrierJump

**Q: Messages not being deleted?**
- Check if message is pinned (pinned messages are never deleted)
- Verify message exists in `scout_systems_posted` table
- Check bot permissions in the scout channel

**Q: Want to see EDDN events?**
- Set `EDDN_DUMP=True` environment variable
- Events will be saved to `./workspace/eddn_events.jsonl`
- File is appended to, so it grows over time

---

## Priority Levels Explained

### Primary Priority
- **Posting Frequency**: Every day
- **Use Case**: Critical systems requiring daily attention
- **Rotation**: None - all Primary systems are posted daily
- **Example**: Systems with active conflicts, high-value targets

### Secondary Priority
- **Posting Frequency**: Every other day (rotated)
- **Use Case**: Important systems that don't need daily attention
- **Rotation**: Systems split into 2 groups, alternating days
- **Example**: Systems being monitored for potential conflicts

### Tertiary Priority
- **Posting Frequency**: Every third day (rotated)
- **Use Case**: Lower priority systems for periodic monitoring
- **Rotation**: Systems split into 3 groups, rotating every 3 days
- **Example**: Long-term monitoring targets, background systems

---

## Workflow Examples

### Setting Up a New Tracking List

1. **Open the tracking modal:**
   ```
   /faction track
   ```

2. **Fill in each priority field** - one system name per line in each text box.

3. **Submit** - the bot validates all names and confirms with a count summary.

4. **Verify the list:**
   ```
   /faction list
   → Download CSV to review all tracked systems
   ```

5. **Launch the scout list:**
   ```
   /faction launch
   → Systems posted to scout channel
   ```

### Updating Tracked Systems

1. **Open the modal** - it is pre-populated with the current list:
   ```
   /faction track
   ```

2. **Edit the text fields** - add, remove, or move systems between priority fields as needed.

3. **Submit** - the full list is replaced atomically.

4. **Reload the scout channel:**
   ```
   /faction launch
   → Updated list posted
   ```

### Changing a System's Priority

1. Open `/faction track` - the modal shows the current list.
2. Delete the system from its current priority field.
3. Add it to the desired priority field.
4. Submit. The system is re-added with the new priority and a fresh `added_at` timestamp.

---

## Technical Details

### System Validation
- Systems must exist in the `systems` table to be added
- The `systems` table contains valid Elite Dangerous star system names
- Validation happens before any systems are added (all-or-nothing validation)
- Invalid systems are reported with specific names

### Caching
- Tracked systems are cached in memory for performance
- Cache is updated when systems are added, removed, or bulk operations occur
- Cache can be force-reloaded if needed
- Cache reduces database queries for frequently accessed data

### Message Management
- When `/faction_launch` is executed, all non-pinned messages in the scout channel are deleted
- Each system is posted as a separate message
- Message IDs are stored in `scout_systems_posted` for tracking
- Pinned messages are preserved during channel purge

### Selection and Limiting
- Systems are sorted by `selection_mode`: `oldest_first` (by `added_at` timestamp) or `absolute` (insertion order)
- Per-priority limits (`primary_limit`, `secondary_limit`, `tertiary_limit`) cap the number of systems posted
- Recently scouted systems are automatically hidden: Secondary within 1 day, Tertiary within 2 days

### Bulk Operations
- Maximum 10 systems per command for safety and performance
- Bulk operations are atomic where possible
- Partial success is reported (e.g., "5 added, 2 failed")
- Operations update cache after completion

---

## Best Practices

1. **System Names**: Use exact system names as they appear in Elite Dangerous. Case-sensitive matching.

2. **Priority Assignment**:
   - Use Primary for systems requiring immediate daily attention
   - Use Secondary for important but not urgent systems
   - Use Tertiary for long-term monitoring

3. **Bulk Operations**: When adding/removing multiple systems, group them by priority to make management easier.

4. **Regular Updates**: Use `/faction_list` periodically to review tracked systems and ensure accuracy.

5. **Launch Timing**: Run `/faction_launch` after making changes to ensure the scout channel reflects current priorities.

6. **Limit Tuning**: Use `primary_limit`, `secondary_limit`, and `tertiary_limit` to control how many systems appear per priority each posting.

---

## Troubleshooting

**Q: System not found when trying to add?**
- Verify the system name is spelled correctly and matches Elite Dangerous exactly
- System must exist in the `systems` validation table
- Check for typos or extra spaces

**Q: Systems not appearing after launch?**
- Verify systems were successfully added using `/faction list`
- Secondary/Tertiary systems scouted recently are automatically hidden (1d and 2d respectively)
- Check whether a per-priority limit is set too low via `/faction config_dump`

**Q: Too many systems appearing?**
- Use per-priority limits: `/faction config name:secondary_limit value:10`
- To reduce the tracked list, open `/faction track`, remove lines from the relevant field, and resubmit
- Export with `/faction list` to review in a spreadsheet

**Q: Want to change a system's priority?**
- Open `/faction track`, move the system name from one priority field to another, and resubmit

**Q: Channel not purging correctly?**
- Pinned messages are never deleted
- Check bot permissions in the scout channel
- Verify the channel ID is correctly configured

**Q: Want to change the order systems are posted?**
- Set `selection_mode` to `oldest_first` to surface the longest-tracked systems first
- Set `selection_mode` to `absolute` to use insertion order
- Use `/faction list` to export and review all tracked systems

---

## Related Commands

- **`/faction config`**: Configure system settings like `selection_mode` and per-priority limits
- **`/faction config_dump`**: View current configuration values

---

## Report Commands

### `/faction_daily_report`
Generates and posts a daily faction state report showing active and pending states for tracked systems.

**Parameters:**
- None

**Behavior:**
1. **Fetches tracked systems** from the database
2. **Retrieves faction states** for each tracked system from the `faction_states` table
3. **Filters states** to only show non-expansion states (wars, elections, civil wars, etc.)
4. **Checks PTN expansion warnings** - shows systems where PTN influence is above 65% (warning) or 70% (danger)
5. **Creates embed** with:
   - Title: "P.T.N. Faction News ™"
   - Footer: GalNet icon and branding
   - Timestamp: Current UTC time
   - Fields: One field per system containing faction states

**Report Content:**
- **PTN Expansion Section**: Shows systems where PTN influence is high (if any)
  - Format: `System Name - status (influence%)`
  - Status: "warning" (>65%) or "danger" (>70%)
- **System Fields**: Each tracked system with non-expansion states gets a field showing:
  - Format: `Faction Name - State Name (Active)` or `(Pending)`
  - Only shows states other than "expansion"
  - Multiple states per faction are shown on separate lines

**Data Source:**
- Faction states are collected from EDDN events when players visit systems
- States are stored in the `faction_states` table
- Data includes: active states, pending states, influence, controlling faction

**Posting:**
- Report is posted to the channel where the command was executed
- If no channel specified, posts to the configured monitoring/report channel
- Command response is ephemeral (only visible to executor)

**Example Output:**
```
P.T.N. Faction News ™

PTN Expansion
Kambarci - danger (72.5%)
LHS 3447 - warning (67.2%)

Kambarci
Pilots Trade Network - War (Active)
Local Faction - Civil War (Pending)
Another Faction - Election (Active)

Sol
Pilots Trade Network - War (Active)
```

**Filtering Logic:**
- Expansion states are excluded from the report (only shown in PTN Expansion section)
- Only tracked systems are included in the report
- Systems with no non-expansion states are not shown
- PTN expansion warnings are shown regardless of tracked status

**Use Cases:**
- Daily monitoring of faction conflicts and states
- Identifying systems requiring attention
- Tracking PTN expansion risk
- Monitoring active wars, elections, and civil wars

---

### `/faction_operations_report`
Generates a classified operations report showing scout activity statistics and exports scout history to CSV.

**Parameters:**
- None

**Behavior:**
1. **Fetches scout history** from the `scout_history` table
2. **Filters to last 3 months** of activity
3. **Counts scouts by username** to identify top performers
4. **Generates embed** with top 5 scouts
5. **Exports CSV file** with complete scout history
6. **Posts both** embed and CSV file

**Report Content:**
- **Embed Title**: "🔍 Faction Operations Report"
- **Description**: Shows total activity count for last 3 months
- **Top 5 Scouts**: Ranked list with medals (🥇🥈🥉🏅)
  - Format: `Medal #Rank Username` → `Count scout reports`
- **Footer**: "[TOP SECRET] Eyes-Only Faction Command"
- **CSV File**: Complete scout history export
  - Filename: `faction_command_eyesonly.csv`
  - Location: `./workspace/faction_command_eyesonly.csv`
  - Contains: id, system_name, username, userid, timestamp

**Data Source:**
- Scout history from `scout_history` table
- Records include:
  - System name that was scouted
  - Username who scouted (or "EDDN" for automated scouts)
  - User ID (0 for EDDN, actual Discord user ID for manual scouts)
  - Timestamp of the scout

**Time Period:**
- Only includes scouts from the last 90 days (3 months)
- Older scouts are excluded from rankings
- CSV export contains ALL scout history (not filtered by time)

**Rankings:**
- Scouts are ranked by total count of scout reports
- Top 5 are displayed with medals
- Ties are handled by sorting order (first occurrence wins)
- Includes both manual scouts (Discord reactions) and automated scouts (EDDN)

**CSV Export:**
- Generated using SQLite export script
- Contains all columns from `scout_history` table
- Headers included in CSV
- Saved to workspace directory
- File is attached to the Discord message

**Response States:**
- **Success**: Embed with top 5 scouts + CSV file attachment
- **No Activity**: Red embed showing "No scout activity recorded in the last 3 months. Asset status: **INACTIVE**"
- **CSV Export Failure**: Embed is still sent, but CSV export fails with warning message
- **Error**: Red embed with error message "Asset compromised. Report failed. Escalate to flight command."

**Example Output:**
```
🔍 Faction Operations Report
Top 5 Scouts (Last 3 Months)
Total Activity: 127 reports

🥇 #1 PilotName
   45 scout reports

🥈 #2 AnotherPilot
   32 scout reports

🥉 #3 ThirdPilot
   28 scout reports

🏅 #4 FourthPilot
   12 scout reports

🏅 #5 FifthPilot
   10 scout reports

[TOP SECRET] Eyes-Only Faction Command
```

**CSV Format:**
```csv
id,system_name,username,userid,timestamp
1,Kambarci,PilotName,123456789,1704067200
2,LHS 3447,EDDN,0,1704070800
3,Sol,AnotherPilot,987654321,1704074400
...
```

**Use Cases:**
- Tracking scout activity and performance
- Identifying top contributors
- Generating reports for faction leadership
- Analyzing scout patterns over time
- Exporting data for external analysis

**Important Notes:**
- Report is classified as "TOP SECRET" and "Eyes-Only Faction Command"
- CSV contains complete history, not just last 3 months
- EDDN scouts are included in rankings (shown as username "EDDN")
- Report can be run in any channel (not restricted to specific channels)

---

## Channel Configuration

The scout channel is configured in `ptn/spyplane/constants.py`:
- **Production**: `PROD_CHANNEL_SCOUT`
- **Testing**: `TEST_CHANNEL_SCOUT`
- Selected based on `PRODUCTION` environment variable

The Faction Scout role ID is also configured:
- **Production**: `PROD_ROLE_SCOUT`
- **Testing**: `TEST_ROLE_SCOUT`
- Used for notifications when launching the scout list

The monitoring/report channel is configured as:
- **Production**: `PROD_CHANNEL_MONITORING`
- **Testing**: `TEST_CHANNEL_MONITORING`
- Used for daily reports and monitoring messages

