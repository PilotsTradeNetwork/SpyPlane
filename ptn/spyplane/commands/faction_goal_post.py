from datetime import datetime, timezone

import discord

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import GOALS_CHANNEL, log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()


def render_goal_template(goalkind: str, system: str, faction_one: str, faction_other: str) -> str:
    """Render a goal template based on goalkind, replacing placeholders with actual values"""
    templates = {
        "RaiseInf": f"Raise INF for __{faction_one}__ to spark the conflict with __{faction_other}__ <:Courier:809221441915977728>",
        "WinElection": f"Win the Election for __{faction_one}__.  <:Partnership:841790422698557520>",
        "WinWar": f"Win the War for __Pilots Trade Network__. <:Assassin:806498760586035200>",
    }
    
    template = templates.get(goalkind, f"Unknown goal kind: {goalkind}")
    return template


@bot.tree.command(name="faction_goal_post")
async def faction_goal_post(interaction: discord.Interaction):
    """Post or update the faction goals embed"""
    await interaction.response.defer()

    repo = FactionGoalsRepository()

    try:
        # Get all goals
        goals = await repo.get_all_goals()

        if not goals:
            await interaction.followup.send(
                "❌ No faction goals found. Add goals using `/faction_goal_add` first."
            )
            return

        # Get the goals channel
        goals_channel = bot.get_channel(GOALS_CHANNEL)
        if not goals_channel:
            await interaction.followup.send(
                "❌ Goals channel not found. Please check bot configuration."
            )
            return

        # Get old message ID and try to delete the old message
        old_message_id = await repo.get_message_id()
        if old_message_id:
            try:
                old_message = await goals_channel.fetch_message(old_message_id)
                if not old_message.pinned:
                    await old_message.delete()
                    log(f"Deleted old faction goals message: {old_message_id}")
            except discord.NotFound:
                log(f"Old message {old_message_id} not found, continuing")
            except Exception as e:
                log(f"Error deleting old message {old_message_id}: {e}")

        # Create embed
        embed = discord.Embed(
            title="🎯 Faction Goals",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc),
        )

        # Add goals to embed
        # Sort by index order
        goals_sorted = sorted(goals, key=lambda x: x[0])

        # Format goals as fields using templates
        for index, system, faction_one, faction_other, goalkind in goals_sorted:
            rendered_template = render_goal_template(goalkind, system, faction_one, faction_other)
            embed.add_field(
                name=f"Goal #{index} - {system}",
                value=rendered_template,
                inline=False,
            )

        embed.set_footer(
            icon_url="https://edassets.org/static/img/pilots-federation/explorer/rank-9.png",
            text="P.T.N. Spy Plane ™",
        )

        # Post the embed to goals channel
        message = await goals_channel.send(embed=embed)

        # Store the new message ID
        await repo.set_message_id(message.id)
        log(f"Posted faction goals embed with message ID: {message.id}")

        await interaction.followup.send(
            "✅ Faction goals embed posted/updated.", ephemeral=True
        )

    except Exception as e:
        log(f"Error posting faction goals: {e}")
        await interaction.followup.send(
            f"❌ Error posting faction goals: {str(e)}"
        )

