from datetime import datetime, timezone

import discord

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.database.faction_states_repository import FactionStatesRepository
from ptn.spyplane.database.systems_repository import SystemsRepository


class DailyFactionStateService:
    def __init__(
        self,
        systems_repo=None,
        faction_states_repo=None,
    ):
        self.systems_repo: SystemsRepository = systems_repo or SystemsRepository()
        self.faction_states_repo: FactionStatesRepository = faction_states_repo or FactionStatesRepository()

    def _has_non_expansion_states(self, active_csv: str, pending_csv: str) -> bool:
        active_states = [s.strip().lower() for s in active_csv.split(",") if s.strip()] if active_csv else []
        pending_states = [s.strip().lower() for s in pending_csv.split(",") if s.strip()] if pending_csv else []

        non_expansion_active = [s for s in active_states if s != "expansion"]
        non_expansion_pending = [s for s in pending_states if s != "expansion"]

        return len(non_expansion_active) > 0 or len(non_expansion_pending) > 0

    def _format_faction_state_simple(self, faction: str, active_csv: str, pending_csv: str) -> list[str]:
        active_states = [s.strip().lower() for s in active_csv.split(",") if s.strip()] if active_csv else []
        pending_states = [s.strip().lower() for s in pending_csv.split(",") if s.strip()] if pending_csv else []

        # Remove expansion from states
        active_without_expansion = [s for s in active_states if s != "expansion"]
        pending_without_expansion = [s for s in pending_states if s != "expansion"]

        # Format: one line per state
        formatted_lines = []
        for state in active_without_expansion:
            formatted_lines.append(f"{faction} - {state} (Active)")
        for state in pending_without_expansion:
            formatted_lines.append(f"{faction} - {state} (Pending)")

        return formatted_lines

    def _get_ptn_status(self, influence: float | None) -> str | None:
        if influence is None:
            return None
        if influence > 0.7:
            return "danger"
        elif influence > 0.65:
            return "warning"
        return None

    async def notify_daily_news(self, systems: list[str] | None = None, channel=None):
        embed = self.common_embed_setup("", "")

        # Get PTN Expansion warnings
        ptn_warnings = await self.faction_states_repo.get_ptn_influence_warnings()
        if ptn_warnings:
            ptn_lines = []
            for system, faction, influence, _controlling in ptn_warnings:
                status = self._get_ptn_status(influence)
                if status:
                    ptn_lines.append(f"{system} - {status} ({influence:.1%})")

            if ptn_lines:
                embed.add_field(name="PTN Expansion", value="\n".join(ptn_lines), inline=False)

        # Get systems to check
        if systems is None:
            tracked = await self.systems_repo.get_all_tracked_systems()
            systems = [s.system for s in tracked]

        # Process each system
        for system in systems:
            try:
                faction_states = await self.faction_states_repo.get_all_faction_states_for_system(system)

                # Filter to only factions with non-expansion states
                # Note: faction_states now returns (system, faction, active, pending, influence, controlling)
                factions_with_states = [
                    (system_name, faction, active, pending)
                    for system_name, faction, active, pending, _, _ in faction_states
                    if self._has_non_expansion_states(active, pending)
                ]

                # Format and add to embed
                if factions_with_states:
                    formatted_states = []
                    for _, faction, active, pending in factions_with_states:
                        formatted_lines = self._format_faction_state_simple(faction, active, pending)
                        formatted_states.extend(formatted_lines)

                    if formatted_states:
                        embed.add_field(name=system, value="\n".join(formatted_states), inline=False)

            except Exception as e:
                log_exception(f"Error processing system {system} for daily report", e)

        bot = get_bot()
        target_channel = channel or bot.report_channel
        if target_channel:
            await target_channel.send(embed=embed)
        else:
            log("No report channel available to send daily faction state report")

    @staticmethod
    def common_embed_setup(description: str, title: str) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            url="https://inara.cz/",
            description=description,
            color=discord.Color.brand_red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(
            icon_url="https://edassets.org/static/img/companies/GalNet.png",
            text="P.T.N. Faction News ™",
        )
        return embed
