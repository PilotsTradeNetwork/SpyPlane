from discord import Interaction

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log

bot = get_bot()


@bot.tree.command()
async def faction_version(interaction: Interaction):
    """Agent experience level"""
    log(f"User {interaction.user.name} requested the version: {__version__}.")
    await interaction.response.send_message(
        f"Bagman is on station and awaiting orders. {bot.user.name} is on version: {__version__}."
    )

