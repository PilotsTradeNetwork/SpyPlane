from discord import Interaction

from ptn.spyplane._metadata import __version__
from ptn.spyplane.constants import log
from ptn.spyplane.spy_plane import bot


@bot.tree.command()
async def faction_version(interaction: Interaction):
    """Agent experience level"""
    log(f"User {interaction.user.name} requested the version: {__version__}.")
    await interaction.response.send_message(
        f"Bagman is on station and awaiting orders. {bot.user.name} is on version: {__version__}."
    )

