from datetime import datetime, timezone
from urllib.parse import quote

import discord

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import EMOJI_ASSASSIN, EMOJI_COURIER, EMOJI_PARTNERSHIP, GOALS_CHANNEL, log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository
from ptn.spyplane.database.faction_header_footer_repository import FactionHeaderFooterRepository

bot = get_bot()


def render_goal_template(goalkind: str, system: str, faction_one: str, faction_other: str) -> str:
    """Render a goal template based on goalkind, replacing placeholders with actual values"""
    # Custom goalkind just returns the custom text directly
    if goalkind == "Custom":
        return faction_one

    templates = {
        "RaiseInf": f"Raise INF for __{faction_one}__ to spark the conflict with __{faction_other}__ <:Courier:{EMOJI_COURIER}>",
        "WinElection": f"Win the Election for __{faction_one}__.  <:partnership:{EMOJI_PARTNERSHIP}>",
        "WinWar": f"Win the War for __Pilots Trade Network__. <:Assassin:{EMOJI_ASSASSIN}>",
        "WinCivilWar": f"Win the Civil war for __{faction_one}__. <:Assassin:{EMOJI_ASSASSIN}>",
    }

    template = templates.get(goalkind, f"Unknown goal kind: {goalkind}")
    return template


@bot.tree.command(name="goal_post")
async def goal_post(interaction: discord.Interaction):
    """Post or update the faction goals embed"""
    await interaction.response.defer(ephemeral=True)

    repo = FactionGoalsRepository()
    header_footer_repo = FactionHeaderFooterRepository()

    try:
        # Get all goals
        goals = await repo.get_all_goals()

        if not goals:
            await interaction.followup.send("❌ No faction goals found. Add goals using `/goal_add` first.")
            return

        # Get the goals channel
        goals_channel = bot.get_channel(GOALS_CHANNEL)
        if not goals_channel:
            await interaction.followup.send("❌ Goals channel not found. Please check bot configuration.")
            return

        # Try to find an existing message to edit
        existing_message = None
        old_message_id = await repo.get_message_id()
        if old_message_id:
            try:
                existing_message = await goals_channel.fetch_message(old_message_id)
            except discord.NotFound:
                log(f"Old message {old_message_id} not found, will post a new one")
            except Exception as e:
                log(f"Error fetching old message {old_message_id}: {e}")

        # Get header and footer
        header, footer_template = await header_footer_repo.get_header_footer()

        # Replace timestamp placeholder in footer with current unix timestamp
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        footer = footer_template.replace("{}", str(current_timestamp))

        # Use header as title, or default if not set
        embed_title = header or "🎯 Faction Goals"

        # Create embed
        embed = discord.Embed(
            title=embed_title,
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc),
        )

        # Set embed author
        embed.set_author(
            name="Director Castro",
            icon_url="https://pilotstradenetwork.com/wp-content/uploads/2021/08/PTN_Dark_wText-768x461.png",
        )

        # Add goals to embed
        # Sort by index order first
        goals_sorted = sorted(goals, key=lambda x: x[0])

        # Group goals by system (maintaining sorted order)
        systems_dict = {}
        for goal in goals_sorted:
            system = goal[1]  # system is at index 1
            if system not in systems_dict:
                systems_dict[system] = []
            systems_dict[system].append(goal)

        # Get unique systems in order of first appearance (which is sorted by index)
        systems_ordered = []
        seen_systems = set()
        for goal in goals_sorted:
            system = goal[1]
            if system not in seen_systems:
                systems_ordered.append(system)
                seen_systems.add(system)

        # Format goals as fields - one field per system
        system_number = 0
        for system in systems_ordered:
            system_number += 1
            system_goals = systems_dict[system]
            system_url = f"https://inara.cz/elite/starsystem/?search={quote(system)}"

            # Build the field value with all goals for this system
            field_value_parts = []

            if len(system_goals) > 1:
                # Multiple goals - add a, b, c prefixes
                for idx, goal in enumerate(system_goals):
                    index, _, faction_one, faction_other, goalkind, additional_note = goal
                    rendered_template = render_goal_template(goalkind, system, faction_one, faction_other)
                    suffix = chr(ord("a") + idx)  # a, b, c, ...
                    field_value_parts.append(f"{suffix}. {rendered_template}")
                    if additional_note:
                        field_value_parts.append(f"    {additional_note}")
            else:
                # Single goal - no prefix needed
                _index, _, faction_one, faction_other, goalkind, additional_note = system_goals[0]
                rendered_template = render_goal_template(goalkind, system, faction_one, faction_other)
                field_value_parts.append(rendered_template)
                if additional_note:
                    field_value_parts.append(f"    {additional_note}")

            # Add system link at the end
            field_value_parts.append(system_url)

            # Create single field for this system
            embed.add_field(
                name=f"{system_number}. {system}",
                value="\n".join(field_value_parts),
                inline=False,
            )

        # Add footer at the bottom as the last field
        if footer:
            embed.add_field(
                name="\u200b",  # Zero-width space to make it appear as footer
                value=footer,
                inline=False,
            )

        embed.set_footer(
            icon_url="https://edassets.org/static/img/pilots-federation/explorer/rank-9.png",
            text="Last Updated",
        )

        # Edit the existing message if we have one, otherwise post a new one
        if existing_message:
            await existing_message.edit(embed=embed)
            log(f"Edited faction goals embed in message ID: {existing_message.id}")
        else:
            existing_message = await goals_channel.send(embed=embed)
            await repo.set_message_id(existing_message.id)
            log(f"Posted new faction goals embed with message ID: {existing_message.id}")

        await interaction.followup.send("✅ Faction goals embed posted/updated.", ephemeral=True)

    except Exception as e:
        log(f"Error posting faction goals: {e}")
        await interaction.followup.send(f"❌ Error posting faction goals: {e!s}")
