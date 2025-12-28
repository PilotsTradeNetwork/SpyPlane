"""
Commands package - imports all commands to register them with the bot
"""
# Import all commands to register them
from ptn.spyplane.commands import faction_ping
from ptn.spyplane.commands import faction_version
from ptn.spyplane.commands import faction_launch
from ptn.spyplane.commands import faction_config_dump
from ptn.spyplane.commands import faction_config
from ptn.spyplane.commands import faction_operations_report
from ptn.spyplane.commands import faction_track
from ptn.spyplane.commands import faction_remove
from ptn.spyplane.commands import faction_removeall
from ptn.spyplane.commands import faction_list


class Commands:
    """Importing this module helps to ensure the annotated methods are registered"""

    def __init__(self):
        pass

