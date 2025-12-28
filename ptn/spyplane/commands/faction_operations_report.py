import asyncio
from asyncio.subprocess import PIPE, STDOUT
from datetime import datetime, timedelta

import discord
from discord import Interaction

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository

bot = get_bot()


async def run_export_script():
    """Run the shell script to export scout history to CSV"""
    cmd = "./ptn/spyplane/scripts/export_scout_history.sh"
    log("[INFO] Starting Export...")
    process = await asyncio.create_subprocess_shell(
        cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT
    )
    await process.wait()
    return process.returncode


@bot.tree.command()
async def faction_operations_report(interaction: Interaction):
    """Top Secret: Classified agent activity report. Faction Command Eyes-Only."""
    await interaction.response.defer()

    try:
        # Get scout history for embed (top 5 scouts)
        three_months_ago = datetime.now() - timedelta(days=90)
        repo = ScoutHistoryRepository()
        scout_history = await repo.get_history()

        # Filter to last 3 months
        recent_scouts = [
            scout for scout in scout_history if scout.timestamp >= three_months_ago
        ]

        # Create embed for top scouts
        if not recent_scouts:
            embed = discord.Embed(
                title="🔍 Faction Operations Report",
                color=discord.Color.red(),
                description="No scout activity recorded in the last 3 months.\nAsset status: **INACTIVE**",
            )
            await interaction.followup.send(embed=embed)
            return

        # Count scouts by username
        scout_counts = {}
        for scout in recent_scouts:
            username = scout.username
            scout_counts[username] = scout_counts.get(username, 0) + 1

        # Get top 5 scouts
        top_scouts = sorted(scout_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Create embed
        embed = discord.Embed(
            title="🔍 Faction Operations Report",
            color=discord.Color.green(),
            description=f"**Top 5 Scouts (Last 3 Months)**\nTotal Activity: {len(recent_scouts)} reports",
        )

        # Add top scouts to embed
        for i, (username, count) in enumerate(top_scouts, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            embed.add_field(
                name=f"{medal} #{i} {username}",
                value=f"**{count}** scout reports",
                inline=False,
            )

        # Add footer with classification
        embed.set_footer(text="[TOP SECRET] Eyes-Only Faction Command")

        # Generate CSV using shell script
        exitcode = await run_export_script()
        if exitcode == 0:
            log("[INFO] Export completed successfully.")
            # Send embed and CSV file
            await interaction.followup.send(
                embed=embed,
                file=discord.File("./workspace/faction_command_eyesonly.csv"),
            )
        else:
            log(f"[INFO] Export failed with exitcode: {exitcode}")
            # Send embed only if CSV export fails
            await interaction.followup.send(embed=embed)
            await interaction.followup.send(
                "⚠️ CSV export failed, but scout rankings are available above."
            )

    except Exception as e:
        log(f"[ERROR] Faction operations report failed: {e}")
        embed = discord.Embed(
            title="🔍 Faction Operations Report",
            color=discord.Color.red(),
            description="Asset compromised. Report failed. Escalate to flight command.",
        )
        await interaction.followup.send(embed=embed)

