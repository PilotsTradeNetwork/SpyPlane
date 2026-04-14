"""Bot registry to avoid circular import issues"""

# Type hint for the bot
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ptn.spyplane.spy_plane import SpyPlane

_bot_instance: Optional["SpyPlane"] = None


def register_bot(bot_instance: "SpyPlane") -> None:
    """Register the bot instance"""
    global _bot_instance
    _bot_instance = bot_instance


def get_bot() -> "SpyPlane":
    """Get the registered bot instance"""
    if _bot_instance is None:
        raise RuntimeError("Bot not registered yet. Call register_bot() first.")
    return _bot_instance
