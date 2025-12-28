"""Journal helper for filtering EDDN events"""


class JournalHelper:
    """Helper class for filtering journal events from EDDN stream"""

    # Events we want to capture
    TARGET_EVENTS = ["FSDJump", "Location", "CarrierJump"]

    @staticmethod
    def is_target_event(json_object: dict) -> bool:
        """
        Check if the event is one of the target events we want to capture.
        
        Args:
            json_object: The parsed EDDN message JSON object
            
        Returns:
            True if the event is FSDJump, Location, or CarrierJump, False otherwise
        """
        try:
            # EDDN messages have structure: {"$schemaRef": "...", "header": {...}, "message": {...}}
            message = json_object.get("message", {})
            event = message.get("event")
            
            return event in JournalHelper.TARGET_EVENTS
        except (AttributeError, KeyError, TypeError):
            return False

