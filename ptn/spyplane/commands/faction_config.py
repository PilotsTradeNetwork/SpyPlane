from discord import Interaction, app_commands

from ptn.spyplane._metadata import __version__
from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.services.config_service import ConfigService

bot = get_bot()


@bot.tree.command(name="faction_config")
@app_commands.describe(
    name="Name of the config: Can be `interval_hours` or `carryover` ",
    value="Value: For `interval_hours` should be a number 1 to 24. For `carryover` it should be `true` or `false`",
)
async def faction_config(interaction: Interaction, name: str, value: str):
    """Assign standard operating protocols"""
    log(
        f"User {interaction.user.name} is attempting to set config {name} to {value}: {__version__}."
    )
    message = await ConfigService().update_config(name, value)
    log(message)
    await interaction.response.send_message(message)

