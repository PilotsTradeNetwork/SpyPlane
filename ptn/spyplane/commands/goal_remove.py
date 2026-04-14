from discord import Interaction, app_commands

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()


@bot.tree.command(name="goal_remove")
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
            # Remove all goals
            count = await repo.remove_all_goals()
            if count > 0:
                await interaction.followup.send(f"✅ Removed all {count} faction goal(s) from the database.")
            else:
                await interaction.followup.send("No goals found to remove.")
            return

        # Remove specific goal by index
        if index is None:
            await interaction.followup.send("❌ Either provide an index or set remove_all to true.")
            return

        # Check if goal exists
        existing = await repo.get_goal_by_index(index)
        if not existing:
            await interaction.followup.send(f"❌ No goal found with index {index}.")
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
            await interaction.followup.send(f"❌ Failed to remove goal with index {index}.")

    except Exception as e:
        log(f"Error removing faction goal: {e}")
        await interaction.followup.send(f"❌ Error removing faction goal: {e!s}")
