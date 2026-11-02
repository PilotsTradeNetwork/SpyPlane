# Faction Goals Commands

## Overview

The `/goal` command group lets the faction team create, edit and display faction objectives in a single Discord
embed in the goals channel. Goals are stored in SQLite, ordered by a unique integer index and grouped by system.
Goals use predefined templates (Raise INF, Win Election/War/Civil War) or free-form custom text.

| Command | Purpose | Response visibility |
|---|---|---|
| `/goal add` | Add a goal via a kind picker + modal | Ephemeral |
| `/goal edit goal_id:<id>` | Edit an existing goal via a kind picker + prefilled modal | Ephemeral |
| `/goal remove [index] [remove_all]` | Remove one goal or all goals | Public |
| `/goal list` | List all goals as a text table | Public |
| `/goal embed` | Edit the embed header and footer | Ephemeral |
| `/goal post` | Post or update the goals embed in the goals channel | Ephemeral |

Permissions are not enforced in code; restrict who can use the commands via Discord's server integration settings.

## Database Structure

### `faction_goals`
- **`index`** (INTEGER PRIMARY KEY): Sort order. Must be unique.
- **`system`** (TEXT NOT NULL): Star system the goal applies to.
- **`faction_one`** (TEXT NOT NULL): Primary faction name, or the goal text for Custom goals.
- **`faction_other`** (TEXT NOT NULL): Opposing faction for RaiseInf goals; empty string otherwise.
- **`goalkind`** (TEXT NOT NULL): `RaiseInf`, `WinElection`, `WinWar`, `WinCivilWar` or `Custom`.
- **`additional_note`** (TEXT): Optional note shown below the goal (not used by Custom goals).

### `faction_header_footer`
- **`id`** (INTEGER PRIMARY KEY, always 1): Single-row table.
- **`header`** (TEXT): Embed title. Seeded with `__Current Short Term Goals__`.
- **`footer`** (TEXT): Text shown at the end of the embed. `{}` is replaced with the current Unix timestamp.

### `configuration`
- **`faction_goals_message_id`**: ID of the posted goals embed message, used by `/goal post` to edit it in place.

## Commands

### `/goal add`
Adds a new faction goal.

**Flow:**
1. Run `/goal add`. An ephemeral dropdown appears with:
   - **Raise INF**: Raise INF to spark conflict
   - **Win Conflict**: Win Election, War, or Civil War
   - **Custom**: Custom multiline text goal
2. Pick a kind; a modal opens.

**Raise INF modal:**
- **Index** (required): Integer, must be unique.
- **System** (required): Max 100 characters.
- **Faction One** (required): Max 100 characters.
- **Faction Other** (optional): Max 100 characters. Adds the "to spark the conflict with ..." part.
- **Additional Note** (optional): Multiline, max 500 characters.

**Win Conflict modal:**
- **Index** (required), **System** (required)
- **Conflict Type** (dropdown): Win Election, Win War or Win Civil War
- **Faction** (required): Max 100 characters.
- **Additional Note** (optional): Multiline, max 500 characters.

**Custom modal:**
- **Index** (required), **System** (required)
- **Custom Text** (required): Multiline, max 1000 characters. Stored in `faction_one`.

**Validation:**
- Index must be an integer and not already in use
- System and faction (or custom text) are required
- All text is trimmed of leading/trailing whitespace

**Example:**
```
/goal add
→ Select "Raise INF"
→ Index: 1
→ System: Kambarci
→ Faction One: Pilots Trade Network
→ Faction Other: Local Faction
→ Additional Note: Focus on delivery missions
```

---

### `/goal edit`
Edits an existing goal.

**Parameters:**
- **`goal_id`** (required): Index of the goal. Autocompletes with `index - goalkind - faction_one`.

**Flow:**
1. Run `/goal edit goal_id:1`. The bot shows the current kind, system and faction, plus a goal kind dropdown.
2. Pick a kind (pick the same kind to keep it). A modal opens prefilled with the current values.
3. Submit to save.

**Behavior:**
- The kind can be changed, e.g. Raise INF to Custom. Fields are prefilled from the existing goal.
- The index can be changed; the new index must not be in use (the goal is re-created under the new index).
- Switching to Custom drops `faction_other` and `additional_note`. Switching to Win Conflict drops `faction_other`.

---

### `/goal remove`
Removes one goal or all goals.

**Parameters:**
- **`index`** (optional): Index of the goal to remove. Required unless `remove_all` is true.
- **`remove_all`** (optional, default `false`): Remove every goal.

**Examples:**
```
/goal remove index:1
→ ✅ Removed faction goal with index 1: System, Faction One, Faction Other

/goal remove remove_all:True
→ ✅ Removed all N faction goal(s) from the database.
```

Errors are reported if the index is missing or not found.

---

### `/goal list`
Lists all goals in a code-block table.

- Columns: Index, System, Faction One, Faction Other, Goal Kind (text truncated to fit)
- Notes are shown on the line below their goal
- Output is split into multiple messages when it exceeds Discord's 2000 character limit

**Example:**
```
Index    System                    Faction One               Faction Other             Goal Kind
----------------------------------------------------------------------------------------------------
1        Kambarci                  Pilots Trade Network      Local Faction             RaiseInf
         Note: Focus on delivery missions
2        Another System            Pilots Trade Network                                WinWar
```

---

### `/goal embed`
Edits the header and footer of the goals embed.

**Flow:**
1. Run `/goal embed`. A modal opens prefilled with the current values:
   - **Header**: Embed title, max 256 characters
   - **Footer**: Text at the end of the embed, max 2000 characters
2. Submit. A blank field keeps its current value (fields cannot be cleared from the modal).

**Footer timestamp placeholder:**
- `{}` in the footer is replaced with the current Unix timestamp on each `/goal post`
- Example: `*Last Updated <t:{}:D>*` becomes `*Last Updated <t:1767102360:D>*`

Changes apply on the next `/goal post`.

---

### `/goal post`
Posts or updates the goals embed in the goals channel (`GOALS_CHANNEL`).

**Behavior:**
1. Fails with an error if there are no goals or the goals channel is not found
2. Looks up the previous embed via `faction_goals_message_id`
3. Builds the embed:
   - **Title**: `faction_header_footer.header` (falls back to `🎯 Faction Goals`)
   - **Author**: "Director Castro" with the PTN logo
   - **Description**: Goals sorted by index and grouped by system (see below)
   - **Field**: The footer text with `{}` replaced by the current timestamp
   - **Embed footer**: "Last Updated" with the post time
4. If the previous message exists, it is **edited in place**. Otherwise a new message is posted and its ID stored.

**Display format:**
- Systems are numbered in order of their lowest goal index (`## 1. Kambarci`)
- A system with several goals lists them as `1.`, `2.`, ...; a single goal is shown without a number
- Notes are shown indented below their goal
- Each system ends with an Inara search link and a dashed separator

**Templates** (emoji IDs come from `constants.py` and differ between prod and test):

| Kind | Rendered text |
|---|---|
| RaiseInf (with Faction Other) | `Raise INF for __{faction_one}__ to spark the conflict with __{faction_other}__ <:Courier:id>` |
| RaiseInf (without Faction Other) | `Raise INF for __{faction_one}__. <:Courier:id>` |
| WinElection | `Win the Election for __{faction_one}__.  <:partnership:id>` |
| WinWar | `Win the War for __{faction_one}__. <:Assassin:id>` |
| WinCivilWar | `Win the Civil war for __{faction_one}__. <:Assassin:id>` |
| Custom | The custom text as-is |

**Example description:**
```
## 1. Kambarci
1. Raise INF for __Pilots Trade Network__ to spark the conflict with __Local Faction__ <:Courier:id>
    Focus on delivery missions
2. Win the Election for __Pilots Trade Network__.  <:partnership:id>
https://inara.cz/elite/starsystem/?search=Kambarci
----------------------------------------
## 2. Another System
Win the War for __Pilots Trade Network__. <:Assassin:id>
https://inara.cz/elite/starsystem/?search=Another%20System
----------------------------------------
```

## Workflow Examples

### Adding and posting goals
```
/goal add → "Raise INF" → Index: 10, System: Kambarci, Faction One: PTN, Faction Other: Local Faction
/goal add → "Win Conflict" → Conflict Type: Win Election, Index: 20, System: Kambarci, Faction: PTN
/goal embed → Header: __Current Short Term Goals__, Footer: ... *Last Updated <t:{}:D>*
/goal post → Both goals shown under "1. Kambarci"
```

### Updating goals
```
/goal edit goal_id:10 → pick kind → change fields → submit
/goal post → Existing embed is edited in place
```

### Clearing all goals
```
/goal remove remove_all:True
/goal post → ❌ No faction goals found
```

## Best Practices

1. **Index spacing**: Use 10, 20, 30... so new goals can be slotted in between.
2. **System names**: Use exact in-game names so the Inara links resolve.
3. **Notes**: Keep them short; the embed description is limited to 4096 characters.
4. **Custom goals**: Use only when no template fits.
5. **Repost**: Run `/goal post` after any add/edit/remove/embed change.
6. **Footer**: Include `{}` in the footer to show when goals were last updated.

## Troubleshooting

**Q: Embed not updating?**
- Run `/goal post` after making changes
- If the old message was deleted, `/goal post` posts a new one automatically

**Q: Can't use a specific index?**
- Indices must be unique. Check with `/goal list`, then edit or remove the conflicting goal

**Q: Footer timestamp not updating?**
- Include `{}` in the footer and run `/goal post`

**Q: Goals in an unexpected order?**
- Systems are ordered by their lowest goal index; goals within a system by index

**Q: Embed failed to post?**
- Check that `GOALS_CHANNEL` in `constants.py` is correct for the environment and the bot can send messages there
- Very long goal lists can exceed Discord's embed limits
