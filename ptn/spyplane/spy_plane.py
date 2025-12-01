import sys
from typing import TYPE_CHECKING

import aiosqlite
from aiosqlite import Connection
from discord import Intents, Object, Emoji
from discord.ext.commands import Bot, when_mentioned_or

if TYPE_CHECKING:
    from asyncio import Lock
    from threading import Thread
    from discord.abc import GuildChannel, PrivateChannel

from ptn.spyplane.constants import GUILD_ID, DB_PATH, log


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
        await self.dbclose()
        await super().close()  # Important! This will log the bot out.

    async def dbclose(self):
        log("closing DB connection")
        if self.db:
            await self.db.close()
        sys.stdout.flush()


bot = SpyPlane()
