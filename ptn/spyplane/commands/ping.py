import random

from ptn_utils.logger.logger import get_logger

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import hello_gifs

logger = get_logger("spyplane.commands.ping")

bot = get_bot()


@bot.command(name="ping", help="Ping the bot")
async def ping(ctx):
    """Ping command that responds with a random hello gif and bot version"""
    logger.info(f"{ctx.author} used PING in {ctx.channel.name}")
    gif = random.choice(hello_gifs)  # noqa: S311
    await ctx.send(f"{gif}\n\nVersion: **{__version__}**")
