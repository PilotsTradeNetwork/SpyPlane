"""
Commands package - imports all commands to register them with the bot
"""

# Import all commands to register them
from ptn.spyplane.commands import (
    faction_config,
    faction_config_dump,
    faction_daily_report,
    faction_launch,
    faction_list,
    faction_operations_report,
    faction_remove,
    faction_removeall,
    faction_track,
    goal_add,
    goal_edit,
    goal_embed,
    goal_list,
    goal_post,
    goal_remove,
    ping,
)

__all__ = [
    "faction_config",
    "faction_config_dump",
    "faction_daily_report",
    "faction_launch",
    "faction_list",
    "faction_operations_report",
    "faction_remove",
    "faction_removeall",
    "faction_track",
    "goal_add",
    "goal_edit",
    "goal_embed",
    "goal_list",
    "goal_post",
    "goal_remove",
    "ping",
]


class Commands:
    """Importing this module helps to ensure the annotated methods are registered"""

    def __init__(self):
        pass
