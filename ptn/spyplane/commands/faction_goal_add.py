from discord import Interaction, app_commands
from discord.app_commands import Choice

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()


@bot.tree.command(name="faction_goal_add")
@app_commands.describe(
    index="Priority index (integer) for this goal",
    system="System name for this goal",
    faction_one="First faction name",
    faction_other="Other faction name",
    goalkind="Type of goal",
)
@app_commands.choices(
    goalkind=[
        Choice(name="Raise Influence", value="RaiseInf"),
        Choice(name="Win Election", value="WinElection"),
        Choice(name="Win War", value="WinWar"),
    ]
)
async def faction_goal_add(
    interaction: Interaction,
    index: int,
    system: str,
    faction_one: str,
    faction_other: str,
    goalkind: str,
):
    """Add a new faction goal to the goals list"""
    await interaction.response.defer()

    repo = FactionGoalsRepository()

    try:
        # Check if goal with this index already exists
        existing = await repo.get_goal_by_index(index)
        if existing:
            await interaction.followup.send(
                f"❌ A goal with index {index} already exists. Use a different index or remove the existing one first."
            )
            return

        # Add the goal
        await repo.add_goal(index, system, faction_one, faction_other, goalkind)

        await interaction.followup.send(
            f"✅ Added faction goal:\n"
            f"**Index:** {index}\n"
            f"**System:** {system}\n"
            f"**Faction One:** {faction_one}\n"
            f"**Faction Other:** {faction_other}\n"
            f"**Goal Kind:** {goalkind}"
        )

    except Exception as e:
        log(f"Error adding faction goal: {e}")
        await interaction.followup.send(
            f"❌ Error adding faction goal: {str(e)}"
        )

