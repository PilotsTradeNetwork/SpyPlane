import asyncio
import os
import random

from discord import Embed, Interaction, Message, RawReactionActionEvent, app_commands
from discord.app_commands import AppCommandError

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import (
    BOT_DEV_CHANNEL,
    CHANNEL_MONITORING,
    CHANNEL_SCOUT,
    EMOJI_TARGET,
    error_gifs,
    hello_gifs,
    log,
    log_exception,
)
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.eddn_listener import get_eddn_listener_thread
from ptn.spyplane.services.post_after_tick_service import PostAfterTickService
from ptn.spyplane.services.scout_recording_service import ScoutRecordingService
from ptn.spyplane.services.scouting_progress_service import get_scouting_progress_service


class DiscordListener:
    """
    Importing this module helps to ensure the annotated methods in this module are registered
    This class prevents the imports optimizer from removing this module
    """

    def __init__(self):
        pass


# Service instances
post_service = PostAfterTickService()
record_service = ScoutRecordingService()
progress_service = get_scouting_progress_service()

# Get bot instance - this is safe because DiscordListener is imported after bot is registered
bot = get_bot()


@bot.event
async def on_ready():
    try:
        log(f"{bot.user.name} has connected to Discord server. Version: {__version__}")

        # Send hello gif to bot dev channel
        botdev_channel = bot.get_channel(BOT_DEV_CHANNEL)
        if botdev_channel:
            embed = Embed(
                title="SPY PLANE ONLINE",
                description=f"<@{bot.user.id}> connected, version **{__version__}**.",
                color=0x00FF00,  # Green color
            )
            embed.set_image(url=random.choice(hello_gifs))  # noqa: S311
            await botdev_channel.send(embed=embed)

        # Set bot.channel to dev channel for reaction handler
        dev_channel = bot.get_channel(CHANNEL_SCOUT)
        bot.channel = dev_channel
        bot.report_channel = bot.get_channel(CHANNEL_MONITORING)
        bot.lock = asyncio.Lock()
        emoji = bot.get_emoji(EMOJI_TARGET)
        bot.emoji_bullseye = emoji or "✅"

        # Load scout systems cache on startup
        repo = SystemsRepository()
        systems = await repo.get_all_tracked_systems()
        log(f"Loaded {len(systems)} scout systems into cache")

        if not post_service.tick_check_and_schedule.is_running():
            post_service.tick_check_and_schedule.start()

        if not progress_service.update_progress_embeds.is_running():
            progress_service.start()

        # Start EDDN listener thread if not already running and not disabled
        eddn_disable = os.getenv("EDDN_DISABLE", "False").lower() == "true"
        if not eddn_disable:
            eddn_listener_thread = get_eddn_listener_thread()
            if not eddn_listener_thread.is_alive():
                eddn_listener_thread.start()
                log("EDDN listener thread started")
        else:
            log("EDDN listener thread disabled via EDDN_DISABLE environment variable")
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
async def on_message(message: Message):
    """Greet if mentioned and ping is written"""
    txt_commands = ["ping"]
    try:
        msg_split = message.content.split()

        # Don't send the gif if any of these conditions is met
        if (
            bot.user.mention not in message.content
            or message.reference
            or message.is_system()
            or message.author is bot.user
        ):
            # Process commands normally
            await bot.process_commands(message)
            return

        # Don't send the gif if a command is detected (even by someone who has no access)
        if len(msg_split) >= 2 and msg_split[1].lower() in txt_commands:
            # Process commands normally
            await bot.process_commands(message)
            return

        # Now that we've ruled out all the cases where we don't want to send the gif, send the gif
        log(f"Bot mentioned in {message.channel.name}, greeting")
        gif = random.choice(hello_gifs)  # noqa: S311
        await message.channel.send(gif, reference=message)
        # Still process commands in case there are other commands
        await bot.process_commands(message)
    except Exception as e:
        log_exception("on_message", e)
        # Still process commands even if there's an error
        await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    try:
        if payload.channel_id != BOT_DEV_CHANNEL:
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
        asyncio.create_task(  # noqa: RUF006
            record_service.record_reaction(message.content, payload.member.name, payload.member.id)
        )  # Another option is to try a Queue
        if not message.pinned:  # prevent deleting pinned messages with reactions in the channel
            await message.delete()
    except Exception as e:
        log_exception("on_raw_reaction_add", e)


@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError):
    """Global error handler for app commands (slash commands)"""
    gif = random.choice(error_gifs)  # noqa: S311

    try:
        log(
            f"Error from {interaction.command.name if interaction.command else 'unknown'} in {interaction.channel.name if interaction.channel else 'unknown'} called by {interaction.user.display_name}: {error}"
        )

        if isinstance(error, (app_commands.MissingPermissions, app_commands.CheckFailure)):
            embed = Embed(
                description="**Permission denied**: You don't have permission to use this command.",
                color=0xFF0000,  # Red color
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception:
                await interaction.followup.send(embed=embed, ephemeral=True)

        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = Embed(
                description=f"**Command on cooldown**: Please try again in {error.retry_after:.2f} seconds.",
                color=0xFF0000,  # Red color
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception:
                await interaction.followup.send(embed=embed, ephemeral=True)

        else:
            # Generic error - send gif and error message
            try:
                await interaction.response.send_message(gif, ephemeral=True)
            except Exception:
                await interaction.followup.send(gif, ephemeral=True)

            embed = Embed(
                description=f"Sorry, that didn't work: {error}",
                color=0xFF0000,  # Red color
            )
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception:
                # If followup also fails, try sending to channel
                if interaction.channel:
                    await interaction.channel.send(embed=embed)

    except Exception as e:
        log_exception("on_app_command_error", e)
        # Last resort - try to send something
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(gif, ephemeral=True)
        except Exception as last_resort_error:
            log_exception("on_app_command_error last resort", last_resort_error)
