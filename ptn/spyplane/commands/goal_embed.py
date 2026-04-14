from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.faction_header_footer_repository import FactionHeaderFooterRepository

bot = get_bot()


class HeaderFooterModal(Modal):
    header_input = TextInput(
        label="Header",
        placeholder="Enter header text (will be used as embed title)",
        style=TextStyle.long,
        required=False,
        max_length=256,
    )

    footer_input = TextInput(
        label="Footer",
        placeholder="Enter footer text. Use {} as placeholder for timestamp.",
        style=TextStyle.long,
        required=False,
        max_length=2000,
    )

    def __init__(self, current_header: str = "", current_footer: str = ""):
        # Ensure values are strings
        current_header = str(current_header) if current_header else ""
        current_footer = str(current_footer) if current_footer else ""

        # Set default values before calling super().__init__()
        self.header_input.default = current_header or None
        self.footer_input.default = current_footer or None

        super().__init__(title="Edit Header and Footer")

        # Store current values to use if fields are left empty
        self.current_header = current_header
        self.current_footer = current_footer

    async def on_submit(self, interaction: Interaction):
        repo = FactionHeaderFooterRepository()

        try:
            # Get values from inputs, or use current values if empty
            header = (
                self.header_input.value.strip()
                if self.header_input.value and self.header_input.value.strip()
                else self.current_header
            )
            footer = (
                self.footer_input.value.strip()
                if self.footer_input.value and self.footer_input.value.strip()
                else self.current_footer
            )

            # Check if anything actually changed
            header_changed = header != self.current_header
            footer_changed = footer != self.current_footer

            if not header_changed and not footer_changed:
                await interaction.response.send_message(
                    "ℹ️ No changes detected. Header and footer remain unchanged.", ephemeral=True
                )
                return

            if header_changed and footer_changed:
                await repo.update_header_footer(header, footer)
                message = "✅ Updated faction goals header and footer"
            elif header_changed:
                await repo.update_header(header)
                message = f"✅ Updated faction goals header:\n{header[:200]}{'...' if len(header) > 200 else ''}"
            else:
                await repo.update_footer(footer)
                message = f"✅ Updated faction goals footer:\n{footer[:200]}{'...' if len(footer) > 200 else ''}"

            await interaction.response.send_message(message, ephemeral=True)

        except Exception as e:
            log(f"Error updating faction goals header/footer: {e}")
            await interaction.response.send_message(
                f"❌ Error updating faction goals header/footer: {e!s}", ephemeral=True
            )


@bot.tree.command(name="goal_embed")
async def goal_embed(interaction: Interaction):
    """Update the header and/or footer text for the faction goals embed"""
    repo = FactionHeaderFooterRepository()

    try:
        # Get current values to pre-populate the modal
        current_header, current_footer = await repo.get_header_footer()

        # Create and populate the modal
        modal = HeaderFooterModal(current_header=current_header, current_footer=current_footer)

        await interaction.response.send_modal(modal)

    except Exception as e:
        log(f"Error opening header/footer modal: {e}")
        await interaction.response.send_message(f"❌ Error opening header/footer editor: {e!s}", ephemeral=True)
