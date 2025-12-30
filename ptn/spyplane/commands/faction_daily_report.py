from discord import Interaction

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.services.daily_faction_state_service import DailyFactionStateService

bot = get_bot()


@bot.tree.command(name="faction_daily_report")
async def faction_daily_report(interaction: Interaction):
    """Generate and post the daily faction state report"""
    await interaction.response.defer()
    
    service = DailyFactionStateService()
    await service.notify_daily_news(channel=interaction.channel)
    
    await interaction.followup.send("✅ Daily faction state report posted", ephemeral=True)

