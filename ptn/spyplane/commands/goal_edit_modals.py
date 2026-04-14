from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput

from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_goals_repository import FactionGoalsRepository


class EditGoalModal(Modal):
    def __init__(self, goal: tuple, new_goalkind: str):
        super().__init__(title="Edit Faction Goal")
        index, system, faction_one, faction_other, _goalkind, additional_note = goal
        self.original_index = index
        self.new_goalkind = new_goalkind

        self.index_input = TextInput(
            label="Index",
            placeholder="Priority index (integer) for this goal",
            default=str(index),
            required=True,
            max_length=10,
        )
        self.system_input = TextInput(
            label="System",
            placeholder="System name for this goal",
            default=system,
            required=True,
            max_length=100,
        )
        self.faction_one_input = TextInput(
            label="Faction One",
            placeholder="First faction name",
            default=faction_one,
            required=True,
            max_length=100,
        )
        self.faction_other_input = TextInput(
            label="Faction Other",
            placeholder="Other faction name (required for RaiseInf)",
            default=faction_other or "",
            required=False,
            max_length=100,
        )
        self.additional_note_input = TextInput(
            label="Additional Note",
            placeholder="Optional additional note for this goal",
            default=additional_note or "",
            style=TextStyle.long,
            required=False,
            max_length=500,
        )

        self.add_item(self.index_input)
        self.add_item(self.system_input)
        self.add_item(self.faction_one_input)
        self.add_item(self.faction_other_input)
        self.add_item(self.additional_note_input)

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()

        try:
            # Validate index
            index_str = self.index_input.value.strip() if self.index_input.value else None
            if not index_str:
                await interaction.response.send_message("❌ Index is required.", ephemeral=True)
                return

            try:
                new_index = int(index_str)
            except ValueError:
                await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
                return

            # If the index changed, check the new index is not already taken
            if new_index != self.original_index:
                existing = await repo.get_goal_by_index(new_index)
                if existing:
                    await interaction.response.send_message(
                        f"❌ A goal with index {new_index} already exists. "
                        "Use a different index or remove the existing one first.",
                        ephemeral=True,
                    )
                    return

            # Validate system
            system = self.system_input.value.strip() if self.system_input.value else None
            if not system:
                await interaction.response.send_message("❌ System is required.", ephemeral=True)
                return

            # Validate faction_one
            faction_one = self.faction_one_input.value.strip() if self.faction_one_input.value else None
            if not faction_one:
                await interaction.response.send_message("❌ Faction One is required.", ephemeral=True)
                return

            faction_other = self.faction_other_input.value.strip() if self.faction_other_input.value else None
            additional_note = self.additional_note_input.value.strip() if self.additional_note_input.value else None

            # RaiseInf requires faction_other
            if self.new_goalkind == "RaiseInf" and not faction_other:
                await interaction.response.send_message(
                    "❌ Faction Other is required for RaiseInf goal kind.", ephemeral=True
                )
                return

            # If the index changed, remove the old record and insert under the new index
            if new_index != self.original_index:
                await repo.remove_goal(self.original_index)
                await repo.add_goal(
                    new_index, system, faction_one, faction_other or "", self.new_goalkind, additional_note
                )
            else:
                updated = await repo.update_goal(
                    self.original_index, system, faction_one, faction_other or "", self.new_goalkind, additional_note
                )
                if not updated:
                    await interaction.response.send_message(
                        f"❌ No goal found with index {self.original_index} to update.", ephemeral=True
                    )
                    return

            response_text = (
                f"✅ Updated faction goal:\n"
                f"**Goal Kind:** {self.new_goalkind}\n"
                f"**Index:** {new_index}\n"
                f"**System:** {system}\n"
                f"**Faction One:** {faction_one}"
            )
            if faction_other:
                response_text += f"\n**Faction Other:** {faction_other}"
            if additional_note:
                response_text += f"\n**Additional Note:** {additional_note}"

            await interaction.response.send_message(response_text, ephemeral=True)

        except Exception as e:
            log(f"Error updating faction goal: {e}")
            await interaction.response.send_message(f"❌ Error updating faction goal: {e!s}", ephemeral=True)


class EditCustomGoalModal(Modal):
    def __init__(self, goal: tuple):
        super().__init__(title="Edit Custom Goal")
        index, system, faction_one, _faction_other, _goalkind, _additional_note = goal
        self.original_index = index

        self.index_input = TextInput(
            label="Index",
            placeholder="Priority index (integer) for this goal",
            default=str(index),
            required=True,
            max_length=10,
        )
        self.system_input = TextInput(
            label="System",
            placeholder="System name for this goal",
            default=system,
            required=True,
            max_length=100,
        )
        self.custom_text_input = TextInput(
            label="Custom Text",
            placeholder="Enter your custom goal text (multiline supported)",
            default=faction_one,
            style=TextStyle.long,
            required=True,
            max_length=1000,
        )

        self.add_item(self.index_input)
        self.add_item(self.system_input)
        self.add_item(self.custom_text_input)

    async def on_submit(self, interaction: Interaction):
        repo = FactionGoalsRepository()

        try:
            # Validate index
            index_str = self.index_input.value.strip() if self.index_input.value else None
            if not index_str:
                await interaction.response.send_message("❌ Index is required.", ephemeral=True)
                return

            try:
                new_index = int(index_str)
            except ValueError:
                await interaction.response.send_message("❌ Index must be a valid integer.", ephemeral=True)
                return

            # If the index changed, check the new index is not already taken
            if new_index != self.original_index:
                existing = await repo.get_goal_by_index(new_index)
                if existing:
                    await interaction.response.send_message(
                        f"❌ A goal with index {new_index} already exists. "
                        "Use a different index or remove the existing one first.",
                        ephemeral=True,
                    )
                    return

            # Validate system
            system = self.system_input.value.strip() if self.system_input.value else None
            if not system:
                await interaction.response.send_message("❌ System is required.", ephemeral=True)
                return

            # Validate custom text
            custom_text = self.custom_text_input.value.strip() if self.custom_text_input.value else None
            if not custom_text:
                await interaction.response.send_message("❌ Custom text is required.", ephemeral=True)
                return

            # If the index changed, remove the old record and insert under the new index
            if new_index != self.original_index:
                await repo.remove_goal(self.original_index)
                await repo.add_goal(new_index, system, custom_text, "", "Custom", None)
            else:
                updated = await repo.update_goal(self.original_index, system, custom_text, "", "Custom", None)
                if not updated:
                    await interaction.response.send_message(
                        f"❌ No goal found with index {self.original_index} to update.", ephemeral=True
                    )
                    return

            response_text = (
                f"✅ Updated custom goal:\n"
                f"**Index:** {new_index}\n"
                f"**System:** {system}\n"
                f"**Custom Text:** {custom_text[:200]}{'...' if len(custom_text) > 200 else ''}"
            )

            await interaction.response.send_message(response_text, ephemeral=True)

        except Exception as e:
            log(f"Error updating custom goal: {e}")
            await interaction.response.send_message(f"❌ Error updating custom goal: {e!s}", ephemeral=True)
