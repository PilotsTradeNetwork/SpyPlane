import asyncio
import sys
from typing import TYPE_CHECKING

import aiosqlite
from aiosqlite import Connection
from discord import Emoji, Intents
from discord.ext.commands import Bot, when_mentioned_or
from discord.ext.prometheus import PrometheusCog
from ptn_utils.get_or_fetch import GetOrFetch
from ptn_utils.global_constants import DISCORD_GUILD, TOKEN, guild_obj
from ptn_utils.logger.logger import get_logger

from ptn.spyplane.bot_registry import register_bot
from ptn.spyplane.constants import DB_PATH, EDDN_URL

if TYPE_CHECKING:
    from asyncio import Lock
    from threading import Thread

    from discord.abc import GuildChannel, PrivateChannel

logger = get_logger("spyplane.bot")


class SpyPlane(Bot):
    def __init__(self):
        intents = Intents.default()
        super().__init__(command_prefix=when_mentioned_or("🕵"), intents=intents)

        self.db: Connection | None = None
        self.lock: Lock | None = None
        self.emoji_bullseye: Emoji | None = None
        self.channel: GuildChannel | Thread | PrivateChannel | None = None
        self.report_channel: GuildChannel | Thread | PrivateChannel | None = None
        self.get_or_fetch: GetOrFetch | None = None

    async def setup_hook(self):
        self.tree.copy_global_to(guild=guild_obj)
        await self.tree.sync(guild=guild_obj)
        logger.info("commands synced")
        await self.dbinit()
        self.get_or_fetch = GetOrFetch(self, DISCORD_GUILD)

    async def dbinit(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.set_trace_callback(logger.trace)
        logger.info("db open")
        sys.stdout.flush()

    async def close(self):
        # Stop EDDN listener thread
        from ptn.spyplane.eddn_listener import get_eddn_listener_thread  # noqa: PLC0415

        eddn_listener_thread = get_eddn_listener_thread()
        if eddn_listener_thread.is_alive():
            logger.info("Stopping EDDN listener thread")
            eddn_listener_thread.stop()
            eddn_listener_thread.join(timeout=5)
        await self.dbclose()
        await super().close()  # Important! This will log the bot out.

    async def dbclose(self):
        logger.info("closing DB connection")
        if self.db:
            await self.db.close()
        sys.stdout.flush()


bot = SpyPlane()
register_bot(bot)  # Register bot after creation


def run():
    # Log EDDN URL as a banner on startup
    banner_width = 60
    border = "=" * banner_width
    logger.info("")
    logger.info(border)
    logger.info(" " * ((banner_width - len("EDDN URL")) // 2) + "EDDN URL")
    logger.info(border)
    logger.info(f"  {EDDN_URL}")
    logger.info(border)
    logger.info("")

    # Import Commands and DiscordListener here to avoid circular import
    from ptn.spyplane.commands import Commands  # noqa: PLC0415
    from ptn.spyplane.discord_listener import DiscordListener  # noqa: PLC0415

    Commands()  # This imports all command modules to register them
    DiscordListener()  # This imports all event handlers to register them
    asyncio.run(spyplane())


async def spyplane():
    await bot.add_cog(PrometheusCog(bot))
    await bot.start(TOKEN)


if __name__ == "__main__":
    run()
