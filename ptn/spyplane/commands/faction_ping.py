from discord import Interaction

from ptn.spyplane.bot_registry import get_bot

bot = get_bot()


@bot.tree.command()
async def faction_ping(interaction: Interaction):
    """Check if assets are blown"""
    await interaction.response.send_message(
        f"**Agent {bot.user.name} reporting in. Ready for clandestine operations**"
    )

