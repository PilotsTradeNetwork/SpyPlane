from discord import Interaction, app_commands

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.systems_repository import SystemsRepository

bot = get_bot()


@bot.tree.command(name="faction_remove")
@app_commands.describe(system_names="Comma-separated list of system names to remove from tracking (max 10 systems)")
async def faction_remove(interaction: Interaction, system_names: str):
    """Remove systems from faction scouting tracking (single or multiple systems)"""
    await interaction.response.defer()

    repo = SystemsRepository()

    try:
        # Parse comma-separated system names
        system_list = [name.strip() for name in system_names.split(",") if name.strip()]

        if len(system_list) == 0:
            await interaction.followup.send("❌ No valid systems found in the list.")
            return

        if len(system_list) > 10:
            await interaction.followup.send("❌ Maximum 10 systems allowed per command.")
            return

        # Bulk remove systems
        successful, failed = await repo.bulk_remove_systems(system_list)

        if successful > 0:
            message = f"✅ Removed {successful} systems from tracking"
            if failed > 0:
                message += f" ({failed} not found)"
            await interaction.followup.send(message)
        else:
            await interaction.followup.send("❌ No systems were removed.")

    except Exception as e:
        log(f"Error processing system names: {e}")
        await interaction.followup.send("❌ Error processing system names.")
