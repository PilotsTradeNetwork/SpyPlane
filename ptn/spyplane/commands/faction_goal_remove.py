from discord import Interaction, app_commands

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()


@bot.tree.command(name="faction_goal_remove")
@app_commands.describe(index="Index of the goal to remove")
async def faction_goal_remove(interaction: Interaction, index: int):
    """Remove a faction goal by its index"""
    await interaction.response.defer()

    repo = FactionGoalsRepository()

    try:
        # Check if goal exists
        existing = await repo.get_goal_by_index(index)
        if not existing:
            await interaction.followup.send(
                f"❌ No goal found with index {index}."
            )
            return

        # Remove the goal
        deleted = await repo.remove_goal(index)

        if deleted:
            await interaction.followup.send(
                f"✅ Removed faction goal with index {index}:\n"
                f"**System:** {existing[1]}\n"
                f"**Faction One:** {existing[2]}\n"
                f"**Faction Other:** {existing[3]}"
            )
        else:
            await interaction.followup.send(
                f"❌ Failed to remove goal with index {index}."
            )

    except Exception as e:
        log(f"Error removing faction goal: {e}")
        await interaction.followup.send(
            f"❌ Error removing faction goal: {str(e)}"
        )

