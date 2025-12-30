import random

from discord.ext import commands

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import hello_gifs, log

bot = get_bot()


@bot.command(name='ping', help='Ping the bot')
async def ping(ctx):
    """Ping command that responds with a random hello gif and bot version"""
    log(f"{ctx.author} used PING in {ctx.channel.name}")
    gif = random.choice(hello_gifs)
    await ctx.send(f"{gif}\n\nVersion: **{__version__}**")

