from discord import Interaction

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.services.systems_posting_service import SystemsPostingService

bot = get_bot()


@bot.tree.command(name="faction_launch")
async def faction_launch(interaction: Interaction):
    """Begin HUMINT and Infiltration operations: Posts the systems to scout in pre-assigned dead drops"""
    await interaction.response.defer(ephemeral=True)
    log(f"User {interaction.user.name} is posting the systems to scout: {__version__}.")
    await SystemsPostingService().publish_systems_to_scout()
    await interaction.followup.send("Spy plane is now on the prowl!")
