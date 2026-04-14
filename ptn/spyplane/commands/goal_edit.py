import discord
from discord import Interaction, app_commands
from discord.ui import Select, View

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.commands.goal_edit_modals import EditCustomGoalModal, EditGoalModal
from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()

GOAL_KIND_OPTIONS = [
    discord.SelectOption(label="Raise Influence", value="RaiseInf", description="Raise INF to spark conflict"),
    discord.SelectOption(label="Win Election", value="WinElection", description="Win the Election"),
    discord.SelectOption(label="Win War", value="WinWar", description="Win the War"),
    discord.SelectOption(label="Win Civil War", value="WinCivilWar", description="Win the Civil War"),
    discord.SelectOption(label="Custom", value="Custom", description="Custom multiline text goal"),
]

# Map stored goalkind values to their display labels for the placeholder
_GOALKIND_LABELS = {opt.value: opt.label for opt in GOAL_KIND_OPTIONS}


class EditGoalKindSelectView(View):
    def __init__(self, goal: tuple):
        super().__init__(timeout=300)  # 5 minute timeout
        self.goal = goal
        _index, _system, _faction_one, _faction_other, current_goalkind, _note = goal

        options = [
            discord.SelectOption(
                label=opt.label,
                value=opt.value,
                description=opt.description,
            )
            for opt in GOAL_KIND_OPTIONS
        ]

        current_label = _GOALKIND_LABELS.get(current_goalkind, current_goalkind)

        self.select = Select(
            placeholder=f"Select a goal kind (current: {current_label})...",
            options=options,
        )
        self.select.callback = self.select_goalkind
        self.add_item(self.select)

    async def select_goalkind(self, interaction: Interaction):
        new_goalkind = self.select.values[0]
        modal = EditCustomGoalModal(self.goal) if new_goalkind == "Custom" else EditGoalModal(self.goal, new_goalkind)
        await interaction.response.send_modal(modal)


async def goal_id_autocomplete(_interaction: Interaction, current: str) -> list[app_commands.Choice[int]]:
    repo = FactionGoalsRepository()
    try:
        goals = await repo.get_all_goals()
    except Exception as e:
        log(f"Error fetching goals for autocomplete: {e}")
        return []

    choices = []
    for index, _system, faction_one, _faction_other, goalkind, _note in goals:
        # Summary shown in the autocomplete dropdown: id - goalkind - faction
        label = f"{index} - {goalkind} - {faction_one}"
        # Truncate to Discord's 100-character limit for choice names
        if len(label) > 100:
            label = label[:97] + "..."
        # Filter by whatever the user has typed so far
        if current == "" or str(index).startswith(current) or current.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=index))

    # Discord allows at most 25 autocomplete choices
    return choices[:25]


@bot.tree.command(name="goal_edit")
@app_commands.describe(goal_id="The ID (index) of the goal to edit")
@app_commands.autocomplete(goal_id=goal_id_autocomplete)
async def goal_edit(interaction: Interaction, goal_id: int):
    """Edit an existing faction goal"""
    try:
        repo = FactionGoalsRepository()
        goal = await repo.get_goal_by_index(goal_id)

        if goal is None:
            await interaction.response.send_message(f"❌ No goal found with index {goal_id}.", ephemeral=True)
            return

        view = EditGoalKindSelectView(goal)
        _index, system, faction_one, _faction_other, goalkind, _note = goal
        await interaction.response.send_message(
            f"Editing goal **#{goal_id}** — current kind: *{goalkind}*, system: **{system}**, faction: {faction_one}\n"
            "Select a goal kind below to open the editor (select the same kind to keep it unchanged):",
            view=view,
            ephemeral=True,
        )
    except Exception as e:
        log(f"Error opening edit goal view: {e}")
        await interaction.response.send_message(f"❌ Error opening goal editor: {e!s}", ephemeral=True)
