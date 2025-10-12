import asyncio
from asyncio.subprocess import PIPE, STDOUT
from discord import Interaction, app_commands
from discord.app_commands import Choice
import discord

from spyplane._metadata import __version__
from spyplane.constants import log
from spyplane.services.config_service import ConfigService
from spyplane.services.systems_posting_service import SystemsPostingService
from spyplane.database.systems_repository import SystemsRepository
from spyplane.spy_plane import bot


class Commands:
    def __init__(self):
        pass


@bot.tree.command()
async def faction_ping(interaction: Interaction):
    """Check if assets are blown"""
    await interaction.response.send_message(
        f"**Agent {bot.user.name} reporting in. Ready for clandestine operations**"
    )


@bot.tree.command()
async def faction_version(interaction: Interaction):
    """Agent experience level"""
    log(f"User {interaction.user.name} requested the version: {__version__}.")
    await interaction.response.send_message(
        f"Bagman is on station and awaiting orders. {bot.user.name} is on version: {__version__}."
    )


@bot.tree.command(name="faction_launch")
async def faction_launch(interaction: Interaction):
    """Begin HUMINT and Infiltration operations: Posts the systems to scout in pre-assigned dead drops"""
    await interaction.response.defer(ephemeral=True)
    log(f"User {interaction.user.name} is posting the systems to scout: {__version__}.")
    await SystemsPostingService().publish_systems_to_scout()
    await interaction.followup.send("Spy plane is now on the prowl!")


@bot.tree.command()
async def faction_config_dump(interaction: Interaction):
    """Playback of standard operating protocols"""
    log(f"User {interaction.user.name} is dumping config: {__version__}.")
    embed = await ConfigService().dump_config_embed()
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="faction_config")
@app_commands.describe(
    name="Name of the config: Can be `interval_hours` or `carryover` ",
    value="Value: For `interval_hours` should be a number 1 to 24. For `carryover` it should be `true` or `false`",
)
async def faction_config(interaction: Interaction, name: str, value: str):
    """Assign standard operating protocols"""
    log(
        f"User {interaction.user.name} is attempting to set config {name} to {value}: {__version__}."
    )
    message = await ConfigService().update_config(name, value)
    log(message)
    await interaction.response.send_message(message)


@bot.tree.command()
async def faction_operations_report(interaction: Interaction):
    """Top Secret: Classified agent activity report. Faction Command Eyes-Only."""
    await interaction.response.defer()
    exitcode = await run_export_script(interaction.channel.send)
    if exitcode == 0:
        log("[INFO] Export completed successfully.")
        await interaction.channel.send(
            file=discord.File("./workspace/faction_command_eyesonly.csv")
        )
        await interaction.followup.send(
            "[Top Secret] Agent Activity Report. Eyes-Only Faction Command"
        )
    else:
        log(f"[INFO] Export failed with exitcode: {exitcode}")
        await interaction.followup.send(
            "Asset compromised. Report failed. Escalate to flight command"
        )


async def run_export_script(send=None):
    cmd = "./export_scout_history.sh"
    log("[INFO] Starting Export...")
    process = await asyncio.create_subprocess_shell(
        cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT
    )
    await process.wait()
    return process.returncode


@bot.tree.command(name="faction_track")
@app_commands.describe(
    system_name="Name of the system to track", priority="Priority level for tracking"
)
@app_commands.choices(
    priority=[
        Choice(name="Primary", value="Primary"),
        Choice(name="Secondary", value="Secondary"),
        Choice(name="Tertiary", value="Tertiary"),
    ]
)
async def faction_track(interaction: Interaction, system_name: str, priority: str):
    """Add a system to track for faction scouting"""
    await interaction.response.defer()

    repo = SystemsRepository()

    # Validate that the system exists in the systems table
    is_valid = await repo.is_valid_system(system_name)
    if not is_valid:
        await interaction.followup.send(
            f"❌ **{system_name}** is not a valid system in our database."
        )
        return

    success = await repo.add_system(system_name, priority, interaction.user.name)

    if success:
        await interaction.followup.send(
            f"✅ Added **{system_name}** to tracking with **{priority}** priority"
        )
    else:
        await interaction.followup.send(
            f"❌ Failed to add **{system_name}**. It may already be tracked."
        )


@bot.tree.command(name="faction_remove")
@app_commands.describe(system_name="Name of the system to remove from tracking")
async def faction_remove(interaction: Interaction, system_name: str):
    """Remove a system from faction scouting tracking"""
    await interaction.response.defer()

    repo = SystemsRepository()
    success = await repo.remove_system(system_name)

    if success:
        await interaction.followup.send(f"✅ Removed **{system_name}** from tracking")
    else:
        await interaction.followup.send(
            f"❌ **{system_name}** was not found in tracked systems"
        )


@bot.tree.command(name="faction_list")
async def faction_list(interaction: Interaction):
    """List all currently tracked systems"""
    await interaction.response.defer()

    repo = SystemsRepository()
    tracked_systems = await repo.get_all_tracked_systems()

    if not tracked_systems:
        await interaction.followup.send("📋 No systems are currently being tracked")
        return

    # Create CSV content
    import csv
    import io
    from datetime import datetime

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["System Name", "Priority", "Added By", "Added At"])

    # Write data
    for system in tracked_systems:
        added_date = datetime.fromtimestamp(system.added_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        writer.writerow([system.system, system.priority, system.added_by, added_date])

    # Create file object
    csv_content = output.getvalue()
    csv_file = io.BytesIO(csv_content.encode("utf-8"))

    # Create Discord file
    discord_file = discord.File(
        csv_file,
        filename=f"tracked_systems_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )

    # Send with summary
    embed = discord.Embed(
        title="📋 Tracked Systems Export",
        color=discord.Color.blue(),
        description=f"Exported {len(tracked_systems)} tracked systems to CSV file",
    )

    # Add summary counts
    primary_count = len([s for s in tracked_systems if s.priority == "Primary"])
    secondary_count = len([s for s in tracked_systems if s.priority == "Secondary"])
    tertiary_count = len([s for s in tracked_systems if s.priority == "Tertiary"])

    embed.add_field(name="🎯 Primary", value=str(primary_count), inline=True)
    embed.add_field(name="⚡ Secondary", value=str(secondary_count), inline=True)
    embed.add_field(name="📊 Tertiary", value=str(tertiary_count), inline=True)

    await interaction.followup.send(embed=embed, file=discord_file)
