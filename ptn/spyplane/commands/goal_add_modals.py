from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput

from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository


class BaseGoalModal(Modal):
    """Base class for goal modals with shared validation logic"""

    index_input = TextInput(
        label="Index",
        placeholder="Priority index (integer) for this goal",
        required=True,
        max_length=10,
    )

    system_input = TextInput(
        label="System",
        placeholder="System name for this goal",
        required=True,
        max_length=100,
    )

    async def validate_common_fields(self, interaction: Interaction) -> tuple[int, str] | None:
        """Validate index and system fields. Returns (index, system) if valid, None otherwise."""
        repo = FactionGoalsRepository()

        # Parse inputs
        index_str = self.index_input.value.strip() if self.index_input.value else None
        system = self.system_input.value.strip() if self.system_input.value else None

        # Validate index
        if not index_str:
            await interaction.response.send_message("❌ Index is required.", ephemeral=True)
            return None

        try:
            index = int(index_str)
        except ValueError:
            await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
            return None

        # Validate system
        if not system:
            await interaction.response.send_message("❌ System is required.", ephemeral=True)
            return None

        # Check if goal with this index already exists
        existing = await repo.get_goal_by_index(index)
        if existing:
            await interaction.response.send_message(
                f"❌ A goal with index {index} already exists. Use a different index or remove the existing one first.",
                ephemeral=True,
            )
            return None

        return (index, system)


class AddGoalModal(BaseGoalModal):
    def __init__(self, goalkind: str):
        super().__init__(title="Add Faction Goal")
        self.goalkind = goalkind

    faction_one_input = TextInput(
        label="Faction One",
        placeholder="First faction name",
        required=True,
        max_length=100,
    )

    faction_other_input = TextInput(
        label="Faction Other",
        placeholder="Other faction name (required for RaiseInf)",
        required=False,
        max_length=100,
    )

    additional_note_input = TextInput(
        label="Additional Note",
        placeholder="Optional additional note for this goal",
        style=TextStyle.long,
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()

        try:
            # Validate common fields (index, system)
            result = await self.validate_common_fields(interaction)
            if result is None:
                return
            index, system = result

            # Parse inputs
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            faction_other = self.faction_other_input.value.strip() if self.faction_other_input.value else None
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None

            # Validate faction_one
            if not faction_one:
                await interaction.response.send_message("❌ Faction One is required.", ephemeral=True)
                return

            # Validate goalkind
            valid_goalkinds = ["RaiseInf", "WinElection", "WinWar", "WinCivilWar", "Custom"]
            if self.goalkind not in valid_goalkinds:
                await interaction.response.send_message(
                    f"❌ Invalid goal kind. Must be one of: {', '.join(valid_goalkinds)}", ephemeral=True
                )
                return

            # RaiseInf requires faction_other
            if self.goalkind == "RaiseInf" and not faction_other:
                await interaction.response.send_message(
                    "❌ Faction Other is required for RaiseInf goal kind.", ephemeral=True
                )
                return

            # Add the goal
            await repo.add_goal(index, system, faction_one, faction_other or "", self.goalkind, additional_note)

            response_text = (
                f"✅ Added faction goal:\n"
                f"**Goal Kind:** {self.goalkind}\n"
                f"**Index:** {index}\n"
                f"**System:** {system}\n"
                f"**Faction One:** {faction_one}"
            )
            if faction_other:
                response_text += f"\n**Faction Other:** {faction_other}"
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"

            await interaction.response.send_message(response_text, ephemeral=True)

        except Exception as e:
            log(f"Error adding faction goal: {e}")
            await interaction.response.send_message(f"❌ Error adding faction goal: {e!s}", ephemeral=True)


class AddCustomGoalModal(BaseGoalModal):
    def __init__(self):
        super().__init__(title="Add Custom Goal")

    custom_text_input = TextInput(
        label="Custom Text",
        placeholder="Enter your custom goal text (multiline supported)",
        style=TextStyle.long,
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()

        try:
            # Validate common fields (index, system)
            result = await self.validate_common_fields(interaction)
            if result is None:
                return
            index, system = result

            # Parse custom text
            custom_text = self.custom_text_input.value.strip() if self.custom_text_input.value else None

            # Validate custom text
            if not custom_text:
                await interaction.response.send_message("❌ Custom text is required.", ephemeral=True)
                return

            # Add the goal - use custom_text as faction_one, empty string for faction_other, no additional note
            await repo.add_goal(index, system, custom_text, "", "Custom", None)

            response_text = (
                f"✅ Added custom goal:\n"
                f"**Index:** {index}\n"
                f"**System:** {system}\n"
                f"**Custom Text:** {custom_text[:200]}{'...' if len(custom_text) > 200 else ''}"
            )

            await interaction.response.send_message(response_text, ephemeral=True)

        except Exception as e:
            log(f"Error adding custom goal: {e}")
            await interaction.response.send_message(f"❌ Error adding custom goal: {e!s}", ephemeral=True)
