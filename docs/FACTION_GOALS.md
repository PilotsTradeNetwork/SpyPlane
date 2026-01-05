# Faction Goals Commands Documentation

## Overview

The Faction Goals system allows administrators to create, manage, and display faction objectives in a Discord embed. Goals are stored in a database and can be organized by priority index and system. The system supports multiple goal types with predefined templates, as well as custom goals with free-form text.

## Database Structure

### `faction_goals` Table
- **`index`** (INTEGER PRIMARY KEY): Priority index for sorting goals. Must be unique.
- **`system`** (TEXT NOT NULL): The star system name where the goal applies.
- **`faction_one`** (TEXT NOT NULL): Primary faction name, or custom text for Custom goals.
- **`faction_other`** (TEXT NOT NULL): Secondary faction name (used for RaiseInf goals).
- **`goalkind`** (TEXT NOT NULL): Type of goal (RaiseInf, WinElection, WinWar, WinCivilWar, Custom).
- **`additional_note`** (TEXT): Optional additional information displayed below the goal.

### `faction_header_footer` Table
- **`id`** (INTEGER PRIMARY KEY): Always 1 (single row table).
- **`header`** (TEXT): Header text displayed as the embed title.
- **`footer`** (TEXT): Footer text with optional `{}` placeholder for Unix timestamp.

## Commands

### `/goal_add`
Adds a new faction goal to the database.

**Usage Flow:**
1. Execute `/goal_add` command
2. Select a goal kind from the dropdown menu:
   - **Raise Influence**: Raise INF to spark conflict
   - **Win Election**: Win the Election
   - **Win War**: Win the War
   - **Win Civil War**: Win the Civil War
   - **Custom**: Custom multiline text goal

3. Fill out the modal form with the required information

**For Standard Goals (RaiseInf, WinElection, WinWar, WinCivilWar):**
- **Index** (required): Integer priority index. Must be unique.
- **System** (required): Star system name (max 100 characters).
- **Faction One** (required): Primary faction name (max 100 characters).
- **Faction Other** (optional): Secondary faction name (max 100 characters). **Required for RaiseInf goals.**
- **Additional Note** (optional): Multiline text for extra context (max 500 characters).

**For Custom Goals:**
- **Index** (required): Integer priority index. Must be unique.
- **System** (required): Star system name (max 100 characters).
- **Custom Text** (required): Multiline text for the goal (max 1000 characters).

**Validation:**
- Index must be a valid integer
- Index must be unique (no duplicate indices allowed)
- System name is required
- For RaiseInf goals, Faction Other is required
- All text fields are trimmed of leading/trailing whitespace

**Example:**
```
/goal_add
→ Select "Raise Influence"
→ Index: 1
→ System: Kambarci
→ Faction One: Pilots Trade Network
→ Faction Other: Local Faction
→ Additional Note: Focus on delivery missions
```

---

### `/goal_remove`
Removes one or all faction goals from the database.

**Parameters:**
- **`index`** (optional): The index of the goal to remove. Required unless `remove_all` is true.
- **`remove_all`** (optional, default: false): If true, removes all goals from the database.

**Usage Examples:**
```
/goal_remove index:1
→ Removes the goal with index 1

/goal_remove remove_all:True
→ Removes all goals from the database
```

**Response:**
- Shows confirmation with the removed goal's details (for single removal)
- Shows count of removed goals (for bulk removal)
- Error message if goal not found or index not provided

---

### `/goal_post`
Posts or updates the faction goals embed in the configured goals channel.

**Behavior:**
1. Fetches all goals from the database
2. Sorts goals by index, then groups by system
3. Deletes the previous embed message (if it exists and isn't pinned)
4. Creates a new embed with:
   - **Title**: From `faction_header_footer.header` (or default "🎯 Faction Goals")
   - **Author**: "Director Castro" with PTN logo
   - **Fields**: One field per system, containing all goals for that system
   - **Footer**: From `faction_header_footer.footer` with timestamp placeholder replaced

**Goal Display Format:**
- Systems are numbered sequentially (1, 2, 3...)
- For systems with multiple goals, each goal gets an alphabetical suffix (a, b, c...)
- System names are clickable links to Inara.cz
- Additional notes appear below their respective goals (indented)
- Footer appears as the last field in the embed

**Goal Templates:**

1. **RaiseInf**: 
   ```
   Raise INF for __{faction_one}__ to spark the conflict with __{faction_other}__ <:Courier:809221441915977728>
   ```

2. **WinElection**: 
   ```
   Win the Election for __{faction_one}__. <:Partnership:841790422698557520>
   ```

3. **WinWar**: 
   ```
   Win the War for __Pilots Trade Network__. <:Assassin:806498760586035200>
   ```

4. **WinCivilWar**: 
   ```
   Win the Civil war for __{faction_one}__. <:Assassin:806498760586035200>
   ```

5. **Custom**: 
   Renders the custom text directly (stored in `faction_one` field)

**Example Embed Structure:**
```
__Current Short Term Goals__

1. Kambarci
   a. Raise INF for __Pilots Trade Network__ to spark the conflict with __Local Faction__ <:Courier:809221441915977728>
      Focus on delivery missions
   b. Win the Election for __Pilots Trade Network__. <:Partnership:841790422698557520>
   https://inara.cz/elite/starsystem/?search=Kambarci

2. Another System
   Win the War for __Pilots Trade Network__. <:Assassin:806498760586035200>
   https://inara.cz/elite/starsystem/?search=Another%20System

[Footer field with note and timestamp]
```

**Message Persistence:**
- The message ID is stored in the `configuration` table
- When posting a new embed, the old one is automatically deleted (unless pinned)
- This ensures only one active goals embed exists at a time

---

### `/goal_embed`
Updates the header and/or footer text for the faction goals embed.

**Usage:**
1. Execute `/goal_embed` command
2. A modal opens with two multiline text fields:
   - **Header**: Text displayed as the embed title (max 256 characters)
   - **Footer**: Text displayed at the bottom (max 2000 characters)
3. Use `{}` as a placeholder in the footer for the Unix timestamp
4. Leave fields empty to keep current values unchanged

**Footer Timestamp Placeholder:**
- Use `{}` in the footer text where you want the timestamp to appear
- The placeholder is replaced with the current Unix timestamp when `/goal_post` is executed
- Example: `*Last Updated <t:{}:D>*` becomes `*Last Updated <t:1767102360:D>*`

**Example:**
```
/goal_embed
→ Header: __Current Short Term Goals__
→ Footer: **__Note__:** Ensure you assess the system... *Last Updated <t:{}:D>*
```

---

### `/goal_list`
Lists all faction goals in a formatted table view.

**Output Format:**
- Displays all goals in a code block table
- Columns: Index, System, Faction One, Faction Other, Goal Kind
- Additional notes are shown below their respective goals (indented)
- Automatically splits into multiple messages if output exceeds Discord's 2000 character limit

**Example Output:**
```
📋 **Faction Goals List**

```
Index    System                    Faction One              Faction Other            Goal Kind      
----------------------------------------------------------------------------------------------------
1        Kambarci                  Pilots Trade Network     Local Faction            RaiseInf        
         Note: Focus on delivery missions
2        Another System            Pilots Trade Network                              WinWar          
```
```

---

## Workflow Examples

### Adding and Posting Goals

1. **Add a goal:**
   ```
   /goal_add → Select "Raise Influence"
   → Index: 1, System: Kambarci, Faction One: PTN, Faction Other: Local Faction
   ```

2. **Add another goal:**
   ```
   /goal_add → Select "Win Election"
   → Index: 2, System: Kambarci, Faction One: PTN
   ```

3. **Set header and footer:**
   ```
   /goal_embed
   → Header: __Current Short Term Goals__
   → Footer: **__Note__:** ... *Last Updated <t:{}:D>*
   ```

4. **Post the embed:**
   ```
   /goal_post
   → Creates embed in goals channel with both goals grouped under "1. Kambarci"
   ```

### Updating Goals

1. **Remove a specific goal:**
   ```
   /goal_remove index:1
   ```

2. **Add a replacement:**
   ```
   /goal_add → [new goal details]
   ```

3. **Repost the embed:**
   ```
   /goal_post
   → Old embed is deleted, new one is posted
   ```

### Clearing All Goals

```
/goal_remove remove_all:True
→ All goals removed
/goal_post
→ Error: No goals found
```

---

## Technical Details

### Goal Index System
- Index is used for sorting goals in the embed
- Lower numbers appear first
- Index must be unique (prevents duplicate priorities)
- You can use any integer values (1, 2, 3... or 10, 20, 30... for spacing)

### System Grouping
- Goals are first sorted by index
- Then grouped by system name
- Systems are numbered sequentially based on first appearance
- Multiple goals in the same system get alphabetical suffixes (a, b, c...)

### Message Management
- Only one active goals embed exists at a time
- Message ID is persisted in the `configuration` table
- Old messages are automatically deleted when posting new ones (unless pinned)
- If the old message is deleted manually, the system continues normally

### Channel Configuration
- Goals are posted to the channel defined by `GOALS_CHANNEL` constant
- Channel ID is environment-specific (production vs testing)
- Configured in `ptn/spyplane/constants.py`

### Error Handling
- All commands provide user-friendly error messages
- Database errors are logged for debugging
- Validation prevents invalid data entry
- Commands are ephemeral (only visible to the user) for privacy

---

## Best Practices

1. **Index Planning**: Use consistent indexing (e.g., 10, 20, 30) to allow easy insertion of goals between existing ones.

2. **System Names**: Use exact system names as they appear in-game for accurate Inara.cz links.

3. **Additional Notes**: Use additional notes sparingly and keep them concise. They appear below goals and can clutter the embed if too long.

4. **Custom Goals**: Reserve custom goals for objectives that don't fit the standard templates. Use templates when possible for consistency.

5. **Regular Updates**: Use `/goal_post` after making changes to ensure the embed reflects current goals.

6. **Footer Timestamp**: Always include the `{}` placeholder in the footer to show when goals were last updated.

---

## Troubleshooting

**Q: Goal embed not updating?**
- Make sure you run `/goal_post` after making changes
- Check that the old message isn't pinned (pinned messages aren't deleted)

**Q: Can't add a goal with a specific index?**
- Index must be unique. Use `/goal_list` to see existing indices
- Remove the conflicting goal first, or use a different index

**Q: Footer timestamp not updating?**
- Make sure you include `{}` in the footer text
- Run `/goal_post` to regenerate the embed with the current timestamp

**Q: Goals not appearing in expected order?**
- Goals are sorted by index first, then grouped by system
- Check your index values with `/goal_list`

**Q: System link not working?**
- System names are URL-encoded automatically
- Verify the system name is spelled correctly

