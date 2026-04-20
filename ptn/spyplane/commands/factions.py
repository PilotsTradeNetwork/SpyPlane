import asyncio
import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import discord
from discord import Interaction, TextStyle, app_commands
from discord.app_commands import Choice
from discord.ui import Modal, TextInput

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.models.scout_system import ScoutSystem
from ptn.spyplane.services.config_service import ConfigService
from ptn.spyplane.services.daily_faction_state_service import DailyFactionStateService
from ptn.spyplane.services.edsm_service import fetch_edsm_systems
from ptn.spyplane.services.systems_posting_service import SystemsPostingService

# -------------
# Command group
# -------------

faction = app_commands.Group(name="faction", description="Faction BGS management commands")


@faction.command(name="config")
@app_commands.describe(
    name="Name of the config: Can be `interval_hours` or `carryover` ",
    value="Value: For `interval_hours` should be a number 1 to 24. For `carryover` it should be `true` or `false`",
)
async def faction_config(interaction: Interaction, name: Literal["interval_hours", "carryover"], value: str):
    """Assign standard operating protocols"""
    log(f"User {interaction.user.name} is attempting to set config {name} to {value}: {__version__}.")
    message = await ConfigService().update_config(name, value)
    log(message)
    await interaction.response.send_message(message)


@faction.command(name="config_dump")
async def faction_config_dump(interaction: Interaction):
    """Playback of standard operating protocols"""
    log(f"User {interaction.user.name} is dumping config: {__version__}.")
    embed = await ConfigService().dump_config_embed()
    await interaction.response.send_message(embed=embed)


@faction.command(name="daily_report")
async def faction_daily_report(interaction: Interaction):
    """Generate and post the daily faction state report"""
    await interaction.response.defer()
    service = DailyFactionStateService()
    await service.notify_daily_news(channel=interaction.channel)
    await interaction.followup.send("✅ Daily faction state report posted", ephemeral=True)


@faction.command(name="launch")
async def faction_launch(interaction: Interaction):
    """Begin HUMINT and Infiltration operations: Posts the systems to scout in pre-assigned dead drops"""
    await interaction.response.defer(ephemeral=True)
    log(f"User {interaction.user.name} is posting the systems to scout: {__version__}.")
    await SystemsPostingService().publish_systems_to_scout()
    await interaction.followup.send("Spy plane is now on the prowl!")


@faction.command(name="list")
async def faction_list(interaction: Interaction):
    """List all currently tracked systems"""
    await interaction.response.defer()
    repo = SystemsRepository()
    tracked_systems = await repo.get_all_tracked_systems()
    if not tracked_systems:
        await interaction.followup.send("📋 No systems are currently being tracked")
        return
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["System Name", "Priority", "Added By", "Added At"])
    for system in tracked_systems:
        added_date = datetime.fromtimestamp(system.added_at, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([system.system, system.priority, system.added_by, added_date])
    csv_content = output.getvalue()
    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    discord_file = discord.File(
        csv_file,
        filename=f"tracked_systems_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
    )
    embed = discord.Embed(
        title="📋 Tracked Systems Export",
        color=discord.Color.blue(),
        description=f"Exported {len(tracked_systems)} tracked systems to CSV file",
    )
    primary_count = len([s for s in tracked_systems if s.priority == "Primary"])
    secondary_count = len([s for s in tracked_systems if s.priority == "Secondary"])
    tertiary_count = len([s for s in tracked_systems if s.priority == "Tertiary"])
    embed.add_field(name="🎯 Primary", value=str(primary_count), inline=True)
    embed.add_field(name="⚡ Secondary", value=str(secondary_count), inline=True)
    embed.add_field(name="📊 Tertiary", value=str(tertiary_count), inline=True)
    await interaction.followup.send(embed=embed, file=discord_file)


@faction.command(name="operations_report")
async def faction_operations_report(interaction: Interaction):
    """Top Secret: Classified agent activity report. Faction Command Eyes-Only."""
    await interaction.response.defer()
    try:
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        repo = ScoutHistoryRepository()
        scout_history = await repo.get_history()
        recent_scouts = [scout for scout in scout_history if scout.timestamp >= three_months_ago]
        if not recent_scouts:
            embed = discord.Embed(
                title="🔍 Faction Operations Report",
                color=discord.Color.red(),
                description="No scout activity recorded in the last 3 months.\nAsset status: **INACTIVE**",
            )
            await interaction.followup.send(embed=embed)
            return
        scout_counts = {}
        for scout in recent_scouts:
            scout_counts[scout.username] = scout_counts.get(scout.username, 0) + 1
        top_scouts = sorted(scout_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        embed = discord.Embed(
            title="🔍 Faction Operations Report",
            color=discord.Color.green(),
            description=f"**Top 5 Scouts (Last 3 Months)**\nTotal Activity: {len(recent_scouts)} reports",
        )
        for i, (username, count) in enumerate(top_scouts, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            embed.add_field(
                name=f"{medal} #{i} {username}",
                value=f"**{count}** scout reports",
                inline=False,
            )
        embed.set_footer(text="[TOP SECRET] Eyes-Only Faction Command")
        exitcode = await run_export_script()
        if exitcode:
            log("[INFO] Export completed successfully.")
            await interaction.followup.send(
                embed=embed,
                file=discord.File("./workspace/faction_command_eyesonly.csv"),
            )
        else:
            log("[INFO] Export failed.")
            await interaction.followup.send(embed=embed)
            await interaction.followup.send("⚠️ CSV export failed, but scout rankings are available above.")
    except Exception as e:
        log(f"[ERROR] Faction operations report failed: {e}")
        embed = discord.Embed(
            title="🔍 Faction Operations Report",
            color=discord.Color.red(),
            description="Asset compromised. Report failed. Escalate to flight command.",
        )
        await interaction.followup.send(embed=embed)


@faction.command(name="track")
async def faction_track(interaction: Interaction):
    """Set the full list of systems to track for faction scouting."""
    repo = SystemsRepository()
    try:
        current_systems = await repo.get_all_tracked_systems()
    except Exception as e:
        log(f"Error loading current systems for faction_track modal: {e}")
        current_systems = []
    await interaction.response.send_modal(FactionTrackModal(current_systems))


bot = get_bot()
bot.tree.add_command(faction)

# ------
# Helper
# ------


async def run_export_script() -> bool:
    log("[INFO] Starting Export...")
    try:
        async with get_bot().db.execute("SELECT * FROM scout_history") as cursor:
            rows = await cursor.fetchall()
            col_names = [description[0] for description in cursor.description]
        with Path("./workspace/faction_command_eyesonly.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            writer.writerows(rows)
        return True
    except Exception as e:
        log(f"[ERROR] Export failed: {e}")
        return False


# -----
# Modal
# -----


class FactionTrackModal(Modal, title="Track Faction Systems"):
    primary_input = TextInput(
        label="Primary Systems",
        placeholder="One system per line",
        style=TextStyle.long,
        required=False,
        max_length=1000,
    )
    secondary_input = TextInput(
        label="Secondary Systems",
        placeholder="One system per line",
        style=TextStyle.long,
        required=False,
        max_length=1000,
    )
    tertiary_input = TextInput(
        label="Tertiary Systems",
        placeholder="One system per line",
        style=TextStyle.long,
        required=False,
        max_length=1000,
    )

    def __init__(self, current_systems: list):
        super().__init__()

        def systems_for_priority(priority: str) -> str:
            return "\n".join(s.system for s in current_systems if s.priority == priority)

        self.primary_input.default = systems_for_priority("Primary")
        self.secondary_input.default = systems_for_priority("Secondary")
        self.tertiary_input.default = systems_for_priority("Tertiary")

    @staticmethod
    def _parse_lines(text: str) -> list[str]:
        if not text:
            return []
        return [line.strip() for line in text.splitlines() if line.strip()]

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()
        repo = SystemsRepository()
        priority_map = {
            "Primary": self._parse_lines(self.primary_input.value),
            "Secondary": self._parse_lines(self.secondary_input.value),
            "Tertiary": self._parse_lines(self.tertiary_input.value),
        }

        all_names = [(priority, name) for priority, names in priority_map.items() for name in names]

        # Check which names exist in the local DB
        db_valid = await asyncio.gather(*[repo.is_valid_system(name) for _, name in all_names])
        db_miss = [all_names[i] for i, valid in enumerate(db_valid) if not valid]

        # Bulk-fetch missing names from EDSM in one request
        edsm_data = await fetch_edsm_systems([name for _, name in db_miss]) if db_miss else {}

        errors: list[str] = []
        far_away: list[tuple[str, str]] = []  # (priority, name)
        unpopulated: list[str] = []

        for priority, name in db_miss:
            system = edsm_data.get(name)
            if system is None:
                errors.append(name)
                continue
            if system.distance > 500 and priority != "Tertiary":
                far_away.append((priority, name))
            if not system.is_populated:
                unpopulated.append(name)

        if errors:
            lines = ["## Errors", f"System(s) not found: {', '.join(errors)}"]
            await interaction.followup.send("\n".join(lines), ephemeral=True)
            return
        try:
            await repo.write_system_to_scout(
                [
                    ScoutSystem(name, priority, interaction.user.name)
                    for priority, names in priority_map.items()
                    for name in names
                ]
            )
        except Exception as e:
            log(f"Error saving tracked systems: {e}")
            await interaction.followup.send("❌ Error saving systems to the database.", ephemeral=True)
            return
        total = sum(len(names) for names in priority_map.values())
        summary_lines = [f"✅ Saved **{total}** tracked system(s):"]
        for priority, names in priority_map.items():
            if names:
                summary_lines.append(f"- **{len(names)}** {priority}")
        if far_away:
            far_names = ", ".join(f"{name} ({p})" for p, name in far_away)
            summary_lines.append(f"\n⚠️ **Distant Systems not in Tertiary List:** {far_names}")
        if unpopulated:
            summary_lines.append(f"⚠️ **Possibly not populated:** {', '.join(unpopulated)}")
        await interaction.followup.send("\n".join(summary_lines))

    async def on_error(self, interaction: Interaction, error: Exception):
        log(f"Error in FactionTrackModal: {error}")
        await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)
