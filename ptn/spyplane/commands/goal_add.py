import discord
from discord import Interaction
from discord.ui import Select, View

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.commands.goal_add_modals import AddGoalModal, AddCustomGoalModal

bot = get_bot()


class GoalKindSelectView(View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minute timeout
    
    @discord.ui.select(
        placeholder="Choose a goal kind...",
        options=[
            discord.SelectOption(label="Raise Influence", value="RaiseInf", description="Raise INF to spark conflict"),
            discord.SelectOption(label="Win Election", value="WinElection", description="Win the Election"),
            discord.SelectOption(label="Win War", value="WinWar", description="Win the War"),
            discord.SelectOption(label="Win Civil War", value="WinCivilWar", description="Win the Civil War"),
            discord.SelectOption(label="Custom", value="Custom", description="Custom multiline text goal"),
        ]
    )
    async def select_goalkind(self, interaction: Interaction, select: Select):
        goalkind = select.values[0]
        if goalkind == "Custom":
            modal = AddCustomGoalModal()
        else:
            modal = AddGoalModal(goalkind=goalkind)
        await interaction.response.send_modal(modal)


@bot.tree.command(name="goal_add")
async def goal_add(interaction: Interaction):
    """Add a new faction goal to the goals list"""
    try:
        view = GoalKindSelectView()
        await interaction.response.send_message(
            "Select a goal kind:",
            view=view,
            ephemeral=True
        )
    except Exception as e:
        log(f"Error opening add goal modal: {e}")
        await interaction.response.send_message(
            f"❌ Error opening goal editor: {str(e)}",
            ephemeral=True
        )

