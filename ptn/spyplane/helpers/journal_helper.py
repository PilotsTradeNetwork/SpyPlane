"""Journal helper for filtering EDDN events"""

from typing import ClassVar

from ptn.spyplane.services.scout_systems_cache import ScoutSystemsCache


class JournalHelper:
    """Helper class for filtering journal events from EDDN stream"""

    # Events we want to capture
    TARGET_EVENTS: ClassVar[list[str]] = ["FSDJump", "Location", "CarrierJump"]

    def __init__(self):
        self.cache = ScoutSystemsCache()

    def is_target_event(self, json_object: dict) -> bool:
        """
        Check if the event is one of the target events AND from a tracked system.

        Args:
            json_object: The parsed EDDN message JSON object

        Returns:
            True if the event is FSDJump, Location, or CarrierJump AND the system is tracked, False otherwise
        """
        try:
            # EDDN messages have structure: {"$schemaRef": "...", "header": {...}, "message": {...}}
            message = json_object.get("message", {})
            event = message.get("event")

            # First check if it's a target event type
            if event not in self.TARGET_EVENTS:
                return False

            # Extract the system name (StarSystem field in the message)
            star_system = message.get("StarSystem")

            if not star_system:
                return False

            # Check if this system is in our tracked systems cache
            tracked_system = self.cache.get(star_system)

            return tracked_system is not None
        except (AttributeError, KeyError, TypeError):
            return False
