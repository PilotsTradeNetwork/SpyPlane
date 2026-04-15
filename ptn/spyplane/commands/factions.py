import csv
import io
from datetime import datetime, timedelta, timezone

import discord
from discord import Interaction, TextStyle, app_commands
from discord.app_commands import Choice
from discord.ui import Modal, TextInput
from ptn_utils.logger.logger import get_logger

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import DATA_DIR_PATH
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.models.scout_system import ScoutSystem
from ptn.spyplane.services.config_service import ConfigService
from ptn.spyplane.services.daily_faction_state_service import DailyFactionStateService
from ptn.spyplane.services.systems_posting_service import SystemsPostingService

# -------------
# Command group
# -------------

logger = get_logger("spyplane.commands.factions")

faction = app_commands.Group(name="faction", description="Faction BGS management commands")


@faction.command(name="config")
@app_commands.describe(
    name="Name of the config: Can be `interval_hours` or `carryover` ",
    value="Value: For `interval_hours` should be a number 1 to 24. For `carryover` it should be `true` or `false`",
)
async def faction_config(interaction: Interaction, name: str, value: str):
    """Assign standard operating protocols"""
    logger.info(f"User {interaction.user.name} is attempting to set config {name} to {value}: {__version__}.")
    message = await ConfigService().update_config(name, value)
    logger.info(message)
    await interaction.response.send_message(message)


@faction.command(name="config_dump")
async def faction_config_dump(interaction: Interaction):
    """Playback of standard operating protocols"""
    logger.info(f"User {interaction.user.name} is dumping config: {__version__}.")
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
    logger.info(f"User {interaction.user.name} is posting the systems to scout: {__version__}.")
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
            logger.info("Export completed successfully.")
            await interaction.followup.send(
                embed=embed,
                file=discord.File(str(DATA_DIR_PATH / "faction_command_eyesonly.csv")),
            )
        else:
            logger.info("Export failed.")
            await interaction.followup.send(embed=embed)
            await interaction.followup.send("⚠️ CSV export failed, but scout rankings are available above.")
    except Exception:
        logger.exception("Faction operations report failed")
        embed = discord.Embed(
            title="🔍 Faction Operations Report",
            color=discord.Color.red(),
            description="Asset compromised. Report failed. Escalate to flight command.",
        )
        await interaction.followup.send(embed=embed)


@faction.command(name="remove")
@app_commands.describe(system_names="Comma-separated list of system names to remove from tracking (max 10 systems)")
async def faction_remove(interaction: Interaction, system_names: str):
    """Remove systems from faction scouting tracking (single or multiple systems)"""
    await interaction.response.defer()
    repo = SystemsRepository()
    try:
        system_list = [name.strip() for name in system_names.split(",") if name.strip()]
        if len(system_list) == 0:
            await interaction.followup.send("❌ No valid systems found in the list.")
            return
        if len(system_list) > 10:
            await interaction.followup.send("❌ Maximum 10 systems allowed per command.")
            return
        successful, failed = await repo.bulk_remove_systems(system_list)
        if successful > 0:
            message = f"✅ Removed {successful} systems from tracking"
            if failed > 0:
                message += f" ({failed} not found)"
            await interaction.followup.send(message)
        else:
            await interaction.followup.send("❌ No systems were removed.")
    except Exception:
        logger.exception("Error processing system names")
        await interaction.followup.send("❌ Error processing system names.")


@faction.command(name="removeall")
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
        deleted_count = await repo.remove_all_by_priority(priority)
        if deleted_count > 0:
            await interaction.followup.send(
                f"✅ Removed all **{priority}** systems from tracking ({deleted_count} systems deleted)"
            )
        else:
            await interaction.followup.send(f"No **{priority}** systems found in tracking")
    except Exception:
        logger.exception(f"Error removing all {priority} systems")
        await interaction.followup.send(f"❌ Error removing all **{priority}** systems from tracking")


@faction.command(name="track")
async def faction_track(interaction: Interaction):
    """Set the full list of systems to track for faction scouting."""
    repo = SystemsRepository()
    try:
        current_systems = await repo.get_all_tracked_systems()
    except Exception:
        logger.exception("Error loading current systems for faction_track modal")
        current_systems = []
    await interaction.response.send_modal(FactionTrackModal(current_systems))


bot = get_bot()
bot.tree.add_command(faction)

# ------
# Helper
# ------


async def run_export_script() -> bool:
    logger.info("Starting Export...")
    try:
        async with get_bot().db.execute("SELECT * FROM scout_history") as cursor:
            rows = await cursor.fetchall()
            col_names = [description[0] for description in cursor.description]
        with (DATA_DIR_PATH / "faction_command_eyesonly.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            writer.writerows(rows)
        return True
    except Exception:
        logger.exception("Export failed")
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
        await interaction.response.defer(ephemeral=True)
        repo = SystemsRepository()
        priority_map = {
            "Primary": self._parse_lines(self.primary_input.value),
            "Secondary": self._parse_lines(self.secondary_input.value),
            "Tertiary": self._parse_lines(self.tertiary_input.value),
        }
        errors: dict[str, list[str]] = {}
        for priority, names in priority_map.items():
            invalid = [name for name in names if not await repo.is_valid_system(name)]
            if invalid:
                errors[priority] = invalid
        if errors:
            lines = ["## Errors"]
            for priority, invalid in errors.items():
                lines.append(f"**{priority}:** {', '.join(invalid)}")
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
        except Exception:
            logger.exception("Error saving tracked systems")
            await interaction.followup.send("❌ Error saving systems to the database.", ephemeral=True)
            return
        total = sum(len(names) for names in priority_map.values())
        summary_lines = [f"✅ Saved **{total}** tracked system(s):"]
        for priority, names in priority_map.items():
            if names:
                summary_lines.append(f"**{priority}:** {', '.join(names)}")
        await interaction.followup.send("\n".join(summary_lines), ephemeral=True)

    async def on_error(self, interaction: Interaction, error: Exception):
        logger.error(f"Error in FactionTrackModal: {error}")
        await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)
