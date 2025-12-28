import asyncio
import sys
from typing import TYPE_CHECKING

import aiosqlite
from aiosqlite import Connection
from discord import Intents, Object, Emoji, RawReactionActionEvent, Message
from discord.ext.commands import Bot, when_mentioned_or

if TYPE_CHECKING:
    from asyncio import Lock
    from threading import Thread
    from discord.abc import GuildChannel, PrivateChannel

from ptn.spyplane._metadata import __version__
from ptn.spyplane.constants import (
    GUILD_ID,
    DB_PATH,
    CONTROL_CHANNEL,
    REPORT_CHANNEL,
    EMOJI_TARGET,
    log,
    log_exception,
)
from discord.ext.prometheus import PrometheusCog

from ptn.spyplane.constants import TOKEN
from ptn.spyplane.eddn_listener import eddn_listener_thread


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

# Service instances - imported after bot creation to avoid circular imports
from ptn.spyplane.services.post_after_tick_service import PostAfterTickService
from ptn.spyplane.services.scout_recording_service import ScoutRecordingService

post_service = PostAfterTickService()
record_service = ScoutRecordingService()


@bot.event
async def on_ready():
    try:
        log(f"{bot.user.name} has connected to Discord server. Version: {__version__}")
        bot.channel = bot.get_channel(CONTROL_CHANNEL)
        bot.report_channel = bot.get_channel(REPORT_CHANNEL)
        bot.lock = asyncio.Lock()
        emoji = bot.get_emoji(EMOJI_TARGET)
        bot.emoji_bullseye = emoji or "✅"
        if not post_service.tick_check_and_schedule.is_running():
            post_service.tick_check_and_schedule.start()

        # Start EDDN listener thread if not already running
        if not eddn_listener_thread.is_alive():
            eddn_listener_thread.start()
            log("EDDN listener thread started")
    except Exception as e:
        log_exception("on_ready", e)

    # Cron in not needed anymore, we are able to read embeds, and BGS Bot messages can trigger spy plane.
    # await bot.channel.send(f'{bot.user.name} has connected to Discord server. Version: {__version__}')
    # @aiocron.crontab('0/10 * * * *')
    # async def tick_cron_job():
    #     await post_service.tick_check_and_schedule()


@bot.event
async def on_disconnect():
    log(f"Spy Plane has disconnected from discord server. Version: {__version__}.")


@bot.event
async def on_error(event, *args, **kwargs):
    log("ERROR")
    log(event)
    log(args)
    log(kwargs)


@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    try:
        if payload.channel_id != CONTROL_CHANNEL:
            # log(f"Not the right channel {payload.channel_id}")
            return
        if payload.user_id == bot.user.id:
            # log(f"Not the right user {payload.user_id}")
            return
        if str(payload.emoji) != str(bot.emoji_bullseye):
            log(
                f"Not the target emoji {payload.emoji} {bot.emoji_bullseye} {payload.emoji.name} {bot.emoji_bullseye.name}"
            )
            return
        message: Message = await bot.channel.fetch_message(payload.message_id)
        asyncio.create_task(
            record_service.record_reaction(
                message.content, payload.member.name, payload.member.id
            )
        )  # Another option is to try a Queue
        if (
            not message.pinned
        ):  # prevent deleting pinned messages with reactions in the channel
            await message.delete()
    except Exception as e:
        log_exception("on_raw_reaction_add", e)


def run():
    # Import Commands here to avoid circular import
    from ptn.spyplane.commands import Commands
    
    Commands()
    asyncio.run(spyplane())


async def spyplane():
    await bot.add_cog(PrometheusCog(bot))
    await bot.start(TOKEN)


if __name__ == "__main__":
    run()
