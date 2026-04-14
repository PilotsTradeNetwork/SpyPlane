from discord import Interaction, app_commands
from discord.app_commands import Choice

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.systems_repository import SystemsRepository

bot = get_bot()


@bot.tree.command(name="faction_track")
@app_commands.describe(
    system_names="Comma-separated list of system names to track (max 10 systems)",
    priority="Priority level for tracking",
)
@app_commands.choices(
    priority=[
        Choice(name="Primary", value="Primary"),
        Choice(name="Secondary", value="Secondary"),
        Choice(name="Tertiary", value="Tertiary"),
    ]
)
async def faction_track(interaction: Interaction, system_names: str, priority: str):
    """Add systems to track for faction scouting (single or multiple systems)"""
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

        # Validate all systems first
        invalid_systems = []
        for system_name in system_list:
            is_valid = await repo.is_valid_system(system_name)
            if not is_valid:
                invalid_systems.append(system_name)

        if invalid_systems:
            await interaction.followup.send(f"❌ Invalid systems found: {', '.join(invalid_systems)}")
            return

        # Prepare systems data (all with same priority)
        systems_data = [(system_name, priority, interaction.user.name) for system_name in system_list]

        # Bulk add systems
        successful, failed = await repo.bulk_add_systems(systems_data)

        if successful > 0:
            message = f"✅ Added {successful} systems to tracking with **{priority}** priority"
            if failed > 0:
                message += f" ({failed} failed)"
            await interaction.followup.send(message)
        else:
            await interaction.followup.send("❌ Failed to add any systems.")

    except Exception as e:
        log(f"Error processing system names: {e}")
        await interaction.followup.send("❌ Error processing system names.")
