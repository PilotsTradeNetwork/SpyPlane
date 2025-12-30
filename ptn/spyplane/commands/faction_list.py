import csv
import io
from datetime import datetime, timezone

import discord
from discord import Interaction

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.database.systems_repository import SystemsRepository

bot = get_bot()


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
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["System Name", "Priority", "Added By", "Added At"])

    # Write data
    for system in tracked_systems:
        added_date = datetime.fromtimestamp(system.added_at, timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        writer.writerow([system.system, system.priority, system.added_by, added_date])

    # Create file object
    csv_content = output.getvalue()
    csv_file = io.BytesIO(csv_content.encode("utf-8"))

    # Create Discord file
    discord_file = discord.File(
        csv_file,
        filename=f"tracked_systems_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
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

