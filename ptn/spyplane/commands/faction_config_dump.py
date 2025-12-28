from discord import Interaction

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.services.config_service import ConfigService

bot = get_bot()


@bot.tree.command()
async def faction_config_dump(interaction: Interaction):
    """Playback of standard operating protocols"""
    log(f"User {interaction.user.name} is dumping config: {__version__}.")
    embed = await ConfigService().dump_config_embed()
    await interaction.response.send_message(embed=embed)

