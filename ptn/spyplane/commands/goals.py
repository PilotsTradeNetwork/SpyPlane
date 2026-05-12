from datetime import datetime, timezone
from urllib.parse import quote

import discord
import discord.ui as ui
from discord import Interaction, TextStyle, app_commands
from discord.ui import Modal, Select, TextInput, View

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import EMOJI_ASSASSIN, EMOJI_COURIER, EMOJI_PARTNERSHIP, GOALS_CHANNEL, log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository
from ptn.spyplane.database.faction_header_footer_repository import FactionHeaderFooterRepository

# --------------------
# Autocomplete helpers
# --------------------


# (must be defined before the group decorators reference them)
async def goal_id_autocomplete(_interaction: Interaction, current: str) -> list[app_commands.Choice[int]]:
    repo = FactionGoalsRepository()
    try:
        goals = await repo.get_all_goals()
    except Exception as e:
        log(f"Error fetching goals for autocomplete: {e}")
        return []
    choices = []
    for index, _system, faction_one, _faction_other, goalkind, _note in goals:
        label = f"{index} - {goalkind} - {faction_one}"
        if len(label) > 100:
            label = label[:97] + "..."
        if current == "" or str(index).startswith(current) or current.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=index))
    return choices[:25]


# -------------
# Command group
# -------------

goal = app_commands.Group(name="goal", description="Faction goal management commands")


@goal.command(name="add")
async def goal_add(interaction: Interaction):
    """Add a new faction goal to the goals list"""
    try:
        view = GoalKindSelectView()
        await interaction.response.send_message("Select a goal kind:", view=view, ephemeral=True)
    except Exception as e:
        log(f"Error opening add goal modal: {e}")
        await interaction.response.send_message(f"❌ Error opening goal editor: {e!s}", ephemeral=True)


@goal.command(name="edit")
@app_commands.describe(goal_id="The ID (index) of the goal to edit")
@app_commands.autocomplete(goal_id=goal_id_autocomplete)
async def goal_edit(interaction: Interaction, goal_id: int):
    """Edit an existing faction goal"""
    try:
        repo = FactionGoalsRepository()
        fetched_goal = await repo.get_goal_by_index(goal_id)
        if fetched_goal is None:
            await interaction.response.send_message(f"❌ No goal found with index {goal_id}.", ephemeral=True)
            return
        view = EditGoalKindSelectView(fetched_goal)
        _index, system, faction_one, _faction_other, goalkind, _note = fetched_goal
        await interaction.response.send_message(
            f"Editing goal **#{goal_id}** — current kind: *{goalkind}*, system: **{system}**, faction: {faction_one}\n"
            "Select a goal kind below to open the editor (select the same kind to keep it unchanged):",
            view=view,
            ephemeral=True,
        )
    except Exception as e:
        log(f"Error opening edit goal view: {e}")
        await interaction.response.send_message(f"❌ Error opening goal editor: {e!s}", ephemeral=True)


@goal.command(name="embed")
async def goal_embed(interaction: Interaction):
    """Update the header and/or footer text for the faction goals embed"""
    repo = FactionHeaderFooterRepository()
    try:
        current_header, current_footer = await repo.get_header_footer()
        modal = HeaderFooterModal(current_header=current_header, current_footer=current_footer)
        await interaction.response.send_modal(modal)
    except Exception as e:
        log(f"Error opening header/footer modal: {e}")
        await interaction.response.send_message(f"❌ Error opening header/footer editor: {e!s}", ephemeral=True)


@goal.command(name="list")
async def goal_list(interaction: Interaction):
    """List all faction goals"""
    await interaction.response.defer()
    repo = FactionGoalsRepository()
    try:
        goals = await repo.get_all_goals()
        if not goals:
            await interaction.followup.send("📋 No goals found in the database.")
            return
        lines = [
            "📋 **Faction Goals List**\n",
            "```",
            f"{'Index':<8} {'System':<25} {'Faction One':<25} {'Faction Other':<25} {'Goal Kind':<15}",
            "-" * 100,
        ]
        for goal_row in goals:
            index, system, faction_one, faction_other, goalkind, additional_note = goal_row
            lines.append(
                f"{index:<8} {system[:24]:<25} {faction_one[:24]:<25} {faction_other[:24]:<25} {goalkind[:14]:<15}"
            )
            if additional_note:
                lines.append(f"         Note: {additional_note[:90] if len(additional_note) > 90 else additional_note}")
        lines.append("```")
        message = "\n".join(lines)
        if len(message) > 2000:
            chunks = []
            current_chunk = []
            current_length = 0
            for line in lines:
                line_length = len(line) + 1
                if current_length + line_length > 1900:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)
    except Exception as e:
        await interaction.followup.send(f"❌ Error listing goals: {e!s}")


@goal.command(name="post")
async def goal_post(interaction: discord.Interaction):
    """Post or update the faction goals embed"""
    await interaction.response.defer(ephemeral=True)
    bot = get_bot()
    repo = FactionGoalsRepository()
    header_footer_repo = FactionHeaderFooterRepository()
    try:
        goals = await repo.get_all_goals()
        if not goals:
            await interaction.followup.send("❌ No faction goals found. Add goals using `/goal add` first.")
            return
        goals_channel = bot.get_channel(GOALS_CHANNEL)
        if not goals_channel:
            await interaction.followup.send("❌ Goals channel not found. Please check bot configuration.")
            return
        existing_message = None
        old_message_id = await repo.get_message_id()
        if old_message_id:
            try:
                existing_message = await goals_channel.fetch_message(old_message_id)
            except discord.NotFound:
                log(f"Old message {old_message_id} not found, will post a new one")
            except Exception as e:
                log(f"Error fetching old message {old_message_id}: {e}")
        header, footer_template = await header_footer_repo.get_header_footer()
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        footer = footer_template.replace("{}", str(current_timestamp))
        embed_title = header or "🎯 Faction Goals"
        embed = discord.Embed(title=embed_title, color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
        embed.set_author(
            name="Director Castro",
            icon_url="https://pilotstradenetwork.com/wp-content/uploads/2021/08/PTN_Dark_wText-768x461.png",
        )
        goals_sorted = sorted(goals, key=lambda x: x[0])
        systems_dict = {}
        for g in goals_sorted:
            system = g[1]
            if system not in systems_dict:
                systems_dict[system] = []
            systems_dict[system].append(g)
        systems_ordered = []
        seen_systems = set()
        for g in goals_sorted:
            system = g[1]
            if system not in seen_systems:
                systems_ordered.append(system)
                seen_systems.add(system)
        description_parts = []
        for system_number, system in enumerate(systems_ordered, start=1):
            system_goals = systems_dict[system]
            system_url = f"https://inara.cz/elite/starsystem/?search={quote(system)}"
            description_parts.append(f"## {system_number}. {system}")
            if len(system_goals) > 1:
                for idx, g in enumerate(system_goals):
                    _index, _, faction_one, faction_other, goalkind, additional_note = g
                    rendered_template = render_goal_template(goalkind, faction_one, faction_other)
                    description_parts.append(f"{idx + 1}. {rendered_template}")
                    if additional_note:
                        description_parts.append(f"    {additional_note}")
            else:
                _index, _, faction_one, faction_other, goalkind, additional_note = system_goals[0]
                rendered_template = render_goal_template(goalkind, faction_one, faction_other)
                description_parts.append(rendered_template)
                if additional_note:
                    description_parts.append(f"    {additional_note}")
            description_parts.append(system_url)
            description_parts.append("-" * 40)
        embed.description = "\n".join(description_parts)
        if footer:
            embed.add_field(name="\u200b", value=footer, inline=False)
        embed.set_footer(
            icon_url="https://edassets.org/static/img/pilots-federation/explorer/rank-9.png", text="Last Updated"
        )
        if existing_message:
            await existing_message.edit(embed=embed)
            log(f"Edited faction goals embed in message ID: {existing_message.id}")
        else:
            existing_message = await goals_channel.send(embed=embed)
            await repo.set_message_id(existing_message.id)
            log(f"Posted new faction goals embed with message ID: {existing_message.id}")
        await interaction.followup.send("✅ Faction goals embed posted/updated.", ephemeral=True)
    except Exception as e:
        log(f"Error posting faction goals: {e}")
        await interaction.followup.send(f"❌ Error posting faction goals: {e!s}")


@goal.command(name="remove")
@app_commands.describe(
    index="Index of the goal to remove (optional if remove_all is true)",
    remove_all="If true, removes all goals from the database",
)
async def goal_remove(interaction: Interaction, index: int | None = None, remove_all: bool = False):
    """Remove a faction goal by its index, or remove all goals"""
    await interaction.response.defer()
    repo = FactionGoalsRepository()
    try:
        if remove_all:
            count = await repo.remove_all_goals()
            if count > 0:
                await interaction.followup.send(f"✅ Removed all {count} faction goal(s) from the database.")
            else:
                await interaction.followup.send("No goals found to remove.")
            return
        if index is None:
            await interaction.followup.send("❌ Either provide an index or set remove_all to true.")
            return
        existing = await repo.get_goal_by_index(index)
        if not existing:
            await interaction.followup.send(f"❌ No goal found with index {index}.")
            return
        deleted = await repo.remove_goal(index)
        if deleted:
            await interaction.followup.send(
                f"✅ Removed faction goal with index {index}:\n**System:** {existing[1]}\n"
                f"**Faction One:** {existing[2]}\n**Faction Other:** {existing[3]}"
            )
        else:
            await interaction.followup.send(f"❌ Failed to remove goal with index {index}.")
    except Exception as e:
        log(f"Error removing faction goal: {e}")
        await interaction.followup.send(f"❌ Error removing faction goal: {e!s}")


# Register the command group
bot = get_bot()
bot.tree.add_command(goal)

# --------------------
# Helpers
# --------------------


def render_goal_template(goalkind: str, faction_one: str, faction_other: str) -> str:
    if goalkind == "Custom":
        return faction_one
    if goalkind == "RaiseInf":
        if faction_other:
            return f"Raise INF for __{faction_one}__ to spark the conflict with __{faction_other}__ <:Courier:{EMOJI_COURIER}>"
        return f"Raise INF for __{faction_one}__. <:Courier:{EMOJI_COURIER}>"
    templates = {
        "WinElection": f"Win the Election for __{faction_one}__.  <:partnership:{EMOJI_PARTNERSHIP}>",
        "WinWar": f"Win the War for __{faction_one}__. <:Assassin:{EMOJI_ASSASSIN}>",
        "WinCivilWar": f"Win the Civil war for __{faction_one}__. <:Assassin:{EMOJI_ASSASSIN}>",
    }
    return templates.get(goalkind, f"Unknown goal kind: {goalkind}")


# -----
# Views
# -----

GOAL_KIND_OPTIONS = [
    discord.SelectOption(label="Raise INF", value="RaiseInf", description="Raise INF to spark conflict"),
    discord.SelectOption(label="Win Conflict", value="WinConflict", description="Win Election, War, or Civil War"),
    discord.SelectOption(label="Custom", value="Custom", description="Custom multiline text goal"),
]
_CONFLICT_KIND_OPTIONS = [
    discord.SelectOption(label="Win Election", value="WinElection"),
    discord.SelectOption(label="Win War", value="WinWar"),
    discord.SelectOption(label="Win Civil War", value="WinCivilWar"),
]
_CONFLICT_KINDS = {"WinElection", "WinWar", "WinCivilWar"}
_GOALKIND_LABELS = {
    "RaiseInf": "Raise INF",
    "WinElection": "Win Election",
    "WinWar": "Win War",
    "WinCivilWar": "Win Civil War",
    "Custom": "Custom",
}


class GoalKindSelectView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.select = Select(
            placeholder="Choose a goal kind...",
            options=[
                discord.SelectOption(label=opt.label, value=opt.value, description=opt.description)
                for opt in GOAL_KIND_OPTIONS
            ],
        )
        self.select.callback = self.select_goalkind
        self.add_item(self.select)

    async def select_goalkind(self, interaction: Interaction):
        goalkind = self.select.values[0]
        if goalkind == "Custom":
            modal = AddCustomGoalModal()
        elif goalkind == "WinConflict":
            modal = AddWinConflictGoalModal()
        else:
            modal = AddGoalModal(goalkind=goalkind)
        await interaction.response.send_modal(modal)


class EditGoalKindSelectView(View):
    def __init__(self, goal: tuple):
        super().__init__(timeout=300)
        self.goal = goal
        _index, _system, _faction_one, _faction_other, current_goalkind, _note = goal
        options = [
            discord.SelectOption(label=opt.label, value=opt.value, description=opt.description)
            for opt in GOAL_KIND_OPTIONS
        ]
        current_label = _GOALKIND_LABELS.get(current_goalkind, current_goalkind)
        self.select = Select(placeholder=f"Select a goal kind (current: {current_label})...", options=options)
        self.select.callback = self.select_goalkind
        self.add_item(self.select)

    async def select_goalkind(self, interaction: Interaction):
        new_goalkind = self.select.values[0]
        if new_goalkind == "Custom":
            modal = EditCustomGoalModal(self.goal)
        elif new_goalkind == "WinConflict":
            modal = EditWinConflictGoalModal(self.goal)
        else:
            modal = EditGoalModal(self.goal, new_goalkind)
        await interaction.response.send_modal(modal)


# -----------------
# Modals — goal add
# -----------------


class BaseGoalModal(Modal):
    index_input = TextInput(
        label="Index", placeholder="Priority index (integer) for this goal", required=True, max_length=10
    )
    system_input = TextInput(label="System", placeholder="System name for this goal", required=True, max_length=100)

    async def validate_common_fields(self, interaction: Interaction) -> tuple[int, str] | None:
        repo = FactionGoalsRepository()
        index_str = self.index_input.value.strip() if self.index_input.value else None
        system = self.system_input.value.strip() if self.system_input.value else None
        if not index_str:
            await interaction.response.send_message("❌ Index is required.", ephemeral=True)
            return None
        try:
            index = int(index_str)
        except ValueError:
            await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
            return None
        if not system:
            await interaction.response.send_message("❌ System is required.", ephemeral=True)
            return None
        existing = await repo.get_goal_by_index(index)
        if existing:
            await interaction.response.send_message(
                f"❌ A goal with index {index} already exists. Use a different index or remove the existing one first.",
                ephemeral=True,
            )
            return None
        return (index, system)


class AddGoalModal(BaseGoalModal):
    def __init__(self, goalkind: str):
        super().__init__(title="Add Faction Goal")
        self.goalkind = goalkind

    faction_one_input = TextInput(label="Faction One", placeholder="First faction name", required=True, max_length=100)
    faction_other_input = TextInput(
        label="Faction Other", placeholder="Other faction name (optional for RaiseInf)", required=False, max_length=100
    )
    additional_note_input = TextInput(
        label="Additional Note",
        placeholder="Optional additional note for this goal",
        style=TextStyle.long,
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            result = await self.validate_common_fields(interaction)
            if result is None:
                return
            index, system = result
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            faction_other = self.faction_other_input.value.strip() if self.faction_other_input.value else None
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None
            if not faction_one:
                await interaction.response.send_message("❌ Faction One is required.", ephemeral=True)
                return
            valid_goalkinds = ["RaiseInf", "WinElection", "WinWar", "WinCivilWar", "Custom"]
            if self.goalkind not in valid_goalkinds:
                await interaction.response.send_message(
                    f"❌ Invalid goal kind. Must be one of: {', '.join(valid_goalkinds)}", ephemeral=True
                )
                return
            # faction_other is optional for RaiseInf
            await repo.add_goal(index, system, faction_one, faction_other or "", self.goalkind, additional_note)
            response_text = (
                f"✅ Added faction goal:\n**Goal Kind:** {self.goalkind}\n**Index:** {index}\n"
                f"**System:** {system}\n**Faction One:** {faction_one}"
            )
            if faction_other:
                response_text += f"\n**Faction Other:** {faction_other}"
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error adding faction goal: {e}")
            await interaction.response.send_message(f"❌ Error adding faction goal: {e!s}", ephemeral=True)


class AddWinConflictGoalModal(BaseGoalModal):
    def __init__(self):
        super().__init__(title="Add Win Conflict Goal")

    conflict_type = ui.Label(
        text="Conflict Type",
        component=ui.Select(
            options=[
                discord.SelectOption(label="Win Election", value="WinElection"),
                discord.SelectOption(label="Win War", value="WinWar"),
                discord.SelectOption(label="Win Civil War", value="WinCivilWar"),
            ]
        ),
    )
    faction_one_input = TextInput(label="Faction", placeholder="Faction name", required=True, max_length=100)
    additional_note_input = TextInput(
        label="Additional Note",
        placeholder="Optional additional note for this goal",
        style=TextStyle.long,
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            result = await self.validate_common_fields(interaction)
            if result is None:
                return
            index, system = result
            goalkind = self.conflict_type.component.values[0]
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None
            if not faction_one:
                await interaction.response.send_message("❌ Faction is required.", ephemeral=True)
                return
            await repo.add_goal(index, system, faction_one, "", goalkind, additional_note)
            response_text = (
                f"✅ Added faction goal:\n**Goal Kind:** {goalkind}\n**Index:** {index}\n"
                f"**System:** {system}\n**Faction:** {faction_one}"
            )
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error adding faction goal: {e}")
            await interaction.response.send_message(f"❌ Error adding faction goal: {e!s}", ephemeral=True)


class AddCustomGoalModal(BaseGoalModal):
    def __init__(self):
        super().__init__(title="Add Custom Goal")

    custom_text_input = TextInput(
        label="Custom Text",
        placeholder="Enter your custom goal text (multiline supported)",
        style=TextStyle.long,
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            result = await self.validate_common_fields(interaction)
            if result is None:
                return
            index, system = result
            custom_text = self.custom_text_input.value.strip() if self.custom_text_input.value else None
            if not custom_text:
                await interaction.response.send_message("❌ Custom text is required.", ephemeral=True)
                return
            await repo.add_goal(index, system, custom_text, "", "Custom", None)
            response_text = (
                f"✅ Added custom goal:\n**Index:** {index}\n**System:** {system}\n"
                f"**Custom Text:** {custom_text[:200]}{'...' if len(custom_text) > 200 else ''}"
            )
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error adding custom goal: {e}")
            await interaction.response.send_message(f"❌ Error adding custom goal: {e!s}", ephemeral=True)


# ------------------
# Modals — goal edit
# ------------------


class EditGoalModal(Modal):
    def __init__(self, goal: tuple, new_goalkind: str):
        super().__init__(title="Edit Faction Goal")
        index, system, faction_one, faction_other, _goalkind, additional_note = goal
        self.original_index = index
        self.new_goalkind = new_goalkind
        self.index_input = TextInput(
            label="Index",
            placeholder="Priority index (integer) for this goal",
            default=str(index),
            required=True,
            max_length=10,
        )
        self.system_input = TextInput(
            label="System", placeholder="System name for this goal", default=system, required=True, max_length=100
        )
        self.faction_one_input = TextInput(
            label="Faction One", placeholder="First faction name", default=faction_one, required=True, max_length=100
        )
        self.faction_other_input = TextInput(
            label="Faction Other",
            placeholder="Other faction name (required for RaiseInf)",
            default=faction_other or "",
            required=False,
            max_length=100,
        )
        self.additional_note_input = TextInput(
            label="Additional Note",
            placeholder="Optional additional note for this goal",
            default=additional_note or "",
            style=TextStyle.long,
            required=False,
            max_length=500,
        )
        self.add_item(self.index_input)
        self.add_item(self.system_input)
        self.add_item(self.faction_one_input)
        self.add_item(self.faction_other_input)
        self.add_item(self.additional_note_input)

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            index_str = self.index_input.value.strip() if self.index_input.value else None
            if not index_str:
                await interaction.response.send_message("❌ Index is required.", ephemeral=True)
                return
            try:
                new_index = int(index_str)
            except ValueError:
                await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
                return
            if new_index != self.original_index:
                existing = await repo.get_goal_by_index(new_index)
                if existing:
                    await interaction.response.send_message(
                        f"❌ A goal with index {new_index} already exists. "
                        "Use a different index or remove the existing one first.",
                        ephemeral=True,
                    )
                    return
            system = self.system_input.value.strip() if self.system_input.value else None
            if not system:
                await interaction.response.send_message("❌ System is required.", ephemeral=True)
                return
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            if not faction_one:
                await interaction.response.send_message("❌ Faction One is required.", ephemeral=True)
                return
            faction_other = self.faction_other_input.value.strip() if self.faction_other_input.value else None
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None
            # faction_other is optional for RaiseInf
            if new_index != self.original_index:
                await repo.remove_goal(self.original_index)
                await repo.add_goal(
                    new_index, system, faction_one, faction_other or "", self.new_goalkind, additional_note
                )
            else:
                updated = await repo.update_goal(
                    self.original_index, system, faction_one, faction_other or "", self.new_goalkind, additional_note
                )
                if not updated:
                    await interaction.response.send_message(
                        f"❌ No goal found with index {self.original_index} to update.", ephemeral=True
                    )
                    return
            response_text = (
                f"✅ Updated faction goal:\n**Goal Kind:** {self.new_goalkind}\n**Index:** {new_index}\n"
                f"**System:** {system}\n**Faction One:** {faction_one}"
            )
            if faction_other:
                response_text += f"\n**Faction Other:** {faction_other}"
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error updating faction goal: {e}")
            await interaction.response.send_message(f"❌ Error updating faction goal: {e!s}", ephemeral=True)


class EditWinConflictGoalModal(Modal):
    def __init__(self, goal: tuple):
        super().__init__(title="Edit Win Conflict Goal")
        index, system, faction_one, _faction_other, current_goalkind, additional_note = goal
        self.original_index = index
        default_kind = current_goalkind if current_goalkind in _CONFLICT_KINDS else "WinElection"
        options = [
            discord.SelectOption(label=opt.label, value=opt.value, default=(opt.value == default_kind))
            for opt in _CONFLICT_KIND_OPTIONS
        ]
        self.index_input = TextInput(
            label="Index",
            placeholder="Priority index (integer) for this goal",
            default=str(index),
            required=True,
            max_length=10,
        )
        self.system_input = TextInput(
            label="System", placeholder="System name for this goal", default=system, required=True, max_length=100
        )
        self.conflict_type = ui.Label(text="Conflict Type", component=ui.Select(options=options))
        self.faction_one_input = TextInput(
            label="Faction", placeholder="Faction name", default=faction_one, required=True, max_length=100
        )
        self.additional_note_input = TextInput(
            label="Additional Note",
            placeholder="Optional additional note for this goal",
            default=additional_note or "",
            style=TextStyle.long,
            required=False,
            max_length=500,
        )
        self.add_item(self.conflict_type)
        self.add_item(self.index_input)
        self.add_item(self.system_input)
        self.add_item(self.faction_one_input)
        self.add_item(self.additional_note_input)

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            new_goalkind = self.conflict_type.component.values[0]
            index_str = self.index_input.value.strip() if self.index_input.value else None
            if not index_str:
                await interaction.response.send_message("❌ Index is required.", ephemeral=True)
                return
            try:
                new_index = int(index_str)
            except ValueError:
                await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
                return
            if new_index != self.original_index:
                existing = await repo.get_goal_by_index(new_index)
                if existing:
                    await interaction.response.send_message(
                        f"❌ A goal with index {new_index} already exists. "
                        "Use a different index or remove the existing one first.",
                        ephemeral=True,
                    )
                    return
            system = self.system_input.value.strip() if self.system_input.value else None
            if not system:
                await interaction.response.send_message("❌ System is required.", ephemeral=True)
                return
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            if not faction_one:
                await interaction.response.send_message("❌ Faction is required.", ephemeral=True)
                return
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None
            if new_index != self.original_index:
                await repo.remove_goal(self.original_index)
                await repo.add_goal(new_index, system, faction_one, "", new_goalkind, additional_note)
            else:
                updated = await repo.update_goal(
                    self.original_index, system, faction_one, "", new_goalkind, additional_note
                )
                if not updated:
                    await interaction.response.send_message(
                        f"❌ No goal found with index {self.original_index} to update.", ephemeral=True
                    )
                    return
            response_text = (
                f"✅ Updated faction goal:\n**Goal Kind:** {new_goalkind}\n**Index:** {new_index}\n"
                f"**System:** {system}\n**Faction:** {faction_one}"
            )
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error updating faction goal: {e}")
            await interaction.response.send_message(f"❌ Error updating faction goal: {e!s}", ephemeral=True)


class EditCustomGoalModal(Modal):
    def __init__(self, goal: tuple):
        super().__init__(title="Edit Custom Goal")
        index, system, faction_one, _faction_other, _goalkind, _additional_note = goal
        self.original_index = index
        self.index_input = TextInput(
            label="Index",
            placeholder="Priority index (integer) for this goal",
            default=str(index),
            required=True,
            max_length=10,
        )
        self.system_input = TextInput(
            label="System", placeholder="System name for this goal", default=system, required=True, max_length=100
        )
        self.custom_text_input = TextInput(
            label="Custom Text",
            placeholder="Enter your custom goal text (multiline supported)",
            default=faction_one,
            style=TextStyle.long,
            required=True,
            max_length=1000,
        )
        self.add_item(self.index_input)
        self.add_item(self.system_input)
        self.add_item(self.custom_text_input)

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()
        try:
            index_str = self.index_input.value.strip() if self.index_input.value else None
            if not index_str:
                await interaction.response.send_message("❌ Index is required.", ephemeral=True)
                return
            try:
                new_index = int(index_str)
            except ValueError:
                await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
                return
            if new_index != self.original_index:
                existing = await repo.get_goal_by_index(new_index)
                if existing:
                    await interaction.response.send_message(
                        f"❌ A goal with index {new_index} already exists. "
                        "Use a different index or remove the existing one first.",
                        ephemeral=True,
                    )
                    return
            system = self.system_input.value.strip() if self.system_input.value else None
            if not system:
                await interaction.response.send_message("❌ System is required.", ephemeral=True)
                return
            custom_text = self.custom_text_input.value.strip() if self.custom_text_input.value else None
            if not custom_text:
                await interaction.response.send_message("❌ Custom text is required.", ephemeral=True)
                return
            if new_index != self.original_index:
                await repo.remove_goal(self.original_index)
                await repo.add_goal(new_index, system, custom_text, "", "Custom", None)
            else:
                updated = await repo.update_goal(self.original_index, system, custom_text, "", "Custom", None)
                if not updated:
                    await interaction.response.send_message(
                        f"❌ No goal found with index {self.original_index} to update.", ephemeral=True
                    )
                    return
            response_text = (
                f"✅ Updated custom goal:\n**Index:** {new_index}\n**System:** {system}\n"
                f"**Custom Text:** {custom_text[:200]}{'...' if len(custom_text) > 200 else ''}"
            )
            await interaction.response.send_message(response_text, ephemeral=True)
        except Exception as e:
            log(f"Error updating custom goal: {e}")
            await interaction.response.send_message(f"❌ Error updating custom goal: {e!s}", ephemeral=True)


# ----------------------------------
# Modal — goal embed (header/footer)
# ----------------------------------


class HeaderFooterModal(Modal):
    header_input = TextInput(
        label="Header",
        placeholder="Enter header text (will be used as embed title)",
        style=TextStyle.long,
        required=False,
        max_length=256,
    )
    footer_input = TextInput(
        label="Footer",
        placeholder="Enter footer text. Use {} as placeholder for timestamp.",
        style=TextStyle.long,
        required=False,
        max_length=2000,
    )

    def __init__(self, current_header: str = "", current_footer: str = ""):
        current_header = str(current_header) if current_header else ""
        current_footer = str(current_footer) if current_footer else ""
        self.header_input.default = current_header or None
        self.footer_input.default = current_footer or None
        super().__init__(title="Edit Header and Footer")
        self.current_header = current_header
        self.current_footer = current_footer

    async def on_submit(self, interaction: Interaction):
        repo = FactionHeaderFooterRepository()
        try:
            header = (
                self.header_input.value.strip()
                if self.header_input.value and self.header_input.value.strip()
                else self.current_header
            )
            footer = (
                self.footer_input.value.strip()
                if self.footer_input.value and self.footer_input.value.strip()
                else self.current_footer
            )
            header_changed = header != self.current_header
            footer_changed = footer != self.current_footer
            if not header_changed and not footer_changed:
                await interaction.response.send_message(
                    "No changes detected. Header and footer remain unchanged.", ephemeral=True
                )
                return
            if header_changed and footer_changed:
                await repo.update_header_footer(header, footer)
                message = "✅ Updated faction goals header and footer"
            elif header_changed:
                await repo.update_header(header)
                message = f"✅ Updated faction goals header:\n{header[:200]}{'...' if len(header) > 200 else ''}"
            else:
                await repo.update_footer(footer)
                message = f"✅ Updated faction goals footer:\n{footer[:200]}{'...' if len(footer) > 200 else ''}"
            await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            log(f"Error updating faction goals header/footer: {e}")
            await interaction.response.send_message(
                f"❌ Error updating faction goals header/footer: {e!s}", ephemeral=True
            )
