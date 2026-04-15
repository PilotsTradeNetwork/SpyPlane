"""
Commands package - imports all commands to register them with the bot
"""

# Import all commands to register them
from . import factions, goals, ping

__all__ = [
    "factions",
    "goals",
    "ping",
]


class Commands:
    """Importing this module helps to ensure the annotated methods are registered"""

    def __init__(self):
        pass
