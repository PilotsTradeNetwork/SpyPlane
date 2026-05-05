import time
from datetime import datetime, timezone

import discord
from discord import Color, Embed

from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.database.systems_repository import SystemsRepository


class ConfigService:
    def __init__(self, repo=None, system_repo=None):
        self.repo = repo or ConfigRepository()
        self.system_repo = system_repo or SystemsRepository()

    async def dump_config_embed(self) -> Embed:
        embed = ConfigService.common_embed_setup(None, "Configuration")
        config_dump = await self.repo.dump_config()
        for config in config_dump:
            embed.add_field(name=config.name, value=config.value, inline=False)
        return embed

    async def update_config(self, name: str, value: str):
        # Note: refactor when we have more configuration options
        name_lower = name.lower()
        value_lower = value.lower()
        supported_configs = [
            "interval_hours",
            "primary_limit",
            "secondary_limit",
            "tertiary_limit",
            "selection_mode",
        ]
        if name_lower not in supported_configs:
            return f"Config was not set. We support only {supported_configs}"
        if name_lower == "interval_hours" and (
            not value_lower.isdigit() or int(value_lower) < 1 or int(value_lower) > 24
        ):
            return "Config was not set. interval_hours supports only numbers between 1 and 24"
        if name_lower in ("primary_limit", "secondary_limit", "tertiary_limit") and (
            not value_lower.isdigit() or int(value_lower) < 0
        ):
            return f"Config was not set. {name_lower} supports only non-negative integers"
        supported_selection_modes = ["oldest_first", "absolute"]
        if name_lower == "selection_mode" and value_lower not in supported_selection_modes:
            return f"Config was not set. selection_mode supports only {supported_selection_modes}"

        await self.repo.update_config(name_lower, value_lower)
        return f"Config {name_lower} was set to {value_lower}"

    @staticmethod
    def common_embed_setup(description, title):
        embed = discord.Embed(
            title=title,
            description=description,
            color=Color.dark_purple(),
            timestamp=datetime.fromtimestamp(time.time(), timezone.utc),
        )
        embed.set_footer(
            icon_url="https://edassets.org/static/img/pilots-federation/explorer/rank-9.png",
            text="P.T.N. Spy Plane ™",
        )
        return embed
