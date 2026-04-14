from discord import Interaction

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository

bot = get_bot()


@bot.tree.command(name="goal_list")
async def goal_list(interaction: Interaction):
    """List all faction goals"""
    await interaction.response.defer()

    repo = FactionGoalsRepository()

    try:
        goals = await repo.get_all_goals()

        if not goals:
            await interaction.followup.send("📋 No goals found in the database.")
            return

        # Build the list message
        lines = []
        lines.append("📋 **Faction Goals List**\n")
        lines.append("```")
        lines.append(f"{'Index':<8} {'System':<25} {'Faction One':<25} {'Faction Other':<25} {'Goal Kind':<15}")
        lines.append("-" * 100)

        for goal in goals:
            index, system, faction_one, faction_other, goalkind, additional_note = goal
            # Truncate long values for table display
            system_display = system[:24] if len(system) > 24 else system
            faction_one_display = faction_one[:24] if len(faction_one) > 24 else faction_one
            faction_other_display = faction_other[:24] if len(faction_other) > 24 else faction_other
            goalkind_display = goalkind[:14] if len(goalkind) > 14 else goalkind

            lines.append(
                f"{index:<8} {system_display:<25} {faction_one_display:<25} {faction_other_display:<25} {goalkind_display:<15}"
            )

            if additional_note:
                note_display = additional_note[:90] if len(additional_note) > 90 else additional_note
                lines.append(f"         Note: {note_display}")

        lines.append("```")

        # Discord message limit is 2000 characters, so split if needed
        message = "\n".join(lines)

        if len(message) > 2000:
            # Split into chunks
            chunks = []
            current_chunk = []
            current_length = 0

            for line in lines:
                line_length = len(line) + 1  # +1 for newline
                if current_length + line_length > 1900:  # Leave some buffer
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length

            if current_chunk:
                chunks.append("\n".join(current_chunk))

            # Send first chunk
            await interaction.followup.send(chunks[0])

            # Send remaining chunks
            for chunk in chunks[1:]:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)

    except Exception as e:
        await interaction.followup.send(f"❌ Error listing goals: {e!s}")
