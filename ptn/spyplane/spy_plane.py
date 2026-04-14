import asyncio
import sys
from typing import TYPE_CHECKING

import aiosqlite
from aiosqlite import Connection
from discord import Emoji, Intents, Object
from discord.ext.commands import Bot, when_mentioned_or

if TYPE_CHECKING:
    from asyncio import Lock
    from threading import Thread

    from discord.abc import GuildChannel, PrivateChannel

from discord.ext.prometheus import PrometheusCog

from ptn.spyplane.bot_registry import register_bot
from ptn.spyplane.constants import (
    DB_PATH,
    EDDN_URL,
    GUILD_ID,
    TOKEN,
    log,
)


class SpyPlane(Bot):
    def __init__(self):
        intents = Intents.default()
        super().__init__(command_prefix=when_mentioned_or("🕵"), intents=intents)

        self.db: Connection | None = None
        self.lock: Lock | None = None
        self.emoji_bullseye: Emoji | None = None
        self.channel: GuildChannel | Thread | PrivateChannel | None = None
        self.report_channel: GuildChannel | Thread | PrivateChannel | None = None

    async def setup_hook(self):
        discord_server_object = Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=discord_server_object)
        await self.tree.sync(guild=discord_server_object)
        log("commands synced")
        await self.dbinit()

    async def dbinit(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.set_trace_callback(log)
        log("db open")
        sys.stdout.flush()

    async def close(self):
        # Stop EDDN listener thread
        from ptn.spyplane.eddn_listener import get_eddn_listener_thread

        eddn_listener_thread = get_eddn_listener_thread()
        if eddn_listener_thread.is_alive():
            log("Stopping EDDN listener thread")
            eddn_listener_thread.stop()
            eddn_listener_thread.join(timeout=5)
        await self.dbclose()
        await super().close()  # Important! This will log the bot out.

    async def dbclose(self):
        log("closing DB connection")
        if self.db:
            await self.db.close()
        sys.stdout.flush()


bot = SpyPlane()
register_bot(bot)  # Register bot after creation


def run():
    # Log EDDN URL as a banner on startup
    banner_width = 60
    border = "=" * banner_width
    log("")
    log(border)
    log(" " * ((banner_width - len("EDDN URL")) // 2) + "EDDN URL")
    log(border)
    log(f"  {EDDN_URL}")
    log(border)
    log("")

    # Import Commands and DiscordListener here to avoid circular import
    from ptn.spyplane.commands import Commands
    from ptn.spyplane.discord_listener import DiscordListener

    Commands()  # This imports all command modules to register them
    DiscordListener()  # This imports all event handlers to register them
    asyncio.run(spyplane())


async def spyplane():
    await bot.add_cog(PrometheusCog(bot))
    await bot.start(TOKEN)


if __name__ == "__main__":
    run()
