from discord import Interaction, app_commands
from discord.app_commands import Choice

from ptn.spyplane.constants import log
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.spy_plane import bot


@bot.tree.command(name="faction_removeall")
@app_commands.describe(priority="Priority level to remove all systems from")
@app_commands.choices(
    priority=[
        Choice(name="Primary", value="Primary"),
        Choice(name="Secondary", value="Secondary"),
        Choice(name="Tertiary", value="Tertiary"),
    ]
)
async def faction_removeall(interaction: Interaction, priority: str):
    """Remove all systems of a specific priority from tracking"""
    await interaction.response.defer()

    repo = SystemsRepository()

    try:
        # Remove all systems of the specified priority
        deleted_count = await repo.remove_all_by_priority(priority)

        if deleted_count > 0:
            await interaction.followup.send(
                f"✅ Removed all **{priority}** systems from tracking ({deleted_count} systems deleted)"
            )
        else:
            await interaction.followup.send(
                f"ℹ️ No **{priority}** systems found in tracking"
            )

    except Exception as e:
        log(f"Error removing all {priority} systems: {e}")
        await interaction.followup.send(
            f"❌ Error removing all **{priority}** systems from tracking"
        )

