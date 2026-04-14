from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.database.faction_states_repository import FactionStatesRepository


class FactionStateService:
    """Service to extract and store faction state data from EDDN events"""

    def __init__(self, repo=None):
        self.repo: FactionStatesRepository = repo or FactionStatesRepository()

    @staticmethod
    def _extract_states(state_list: list) -> str:
        """Extract state names from a list of state objects or strings"""
        states = [
            state_obj.get("State") if isinstance(state_obj, dict) else state_obj
            for state_obj in state_list
            if state_obj and (state_obj.get("State") if isinstance(state_obj, dict) else state_obj)
        ]
        return ",".join(states)

    def extract_faction_states_from_event(self, json_data: dict) -> list[dict]:
        try:
            message = json_data.get("message", {})
            star_system = message.get("StarSystem")

            if not star_system:
                log("EDDN event missing StarSystem field for faction state extraction")
                return []

            controlling_faction_name = None
            system_faction = message.get("SystemFaction")
            if system_faction and isinstance(system_faction, dict):
                controlling_faction_name = system_faction.get("Name")

            return [
                {
                    "system": star_system,
                    "faction": faction.get("Name"),
                    "active_csv": self._extract_states(faction.get("ActiveStates", [])),
                    "pending_csv": self._extract_states(faction.get("PendingStates", [])),
                    "influence": faction.get("Influence"),
                    "controlling": 1 if faction.get("Name") == controlling_faction_name else 0,
                }
                for faction in message.get("Factions", [])
                if faction.get("Name")
            ]
        except Exception as e:
            log_exception("Error extracting faction states from EDDN event", e)
            return []

    async def replace_faction_states_from_event(self, json_data: dict) -> None:
        try:
            faction_states = self.extract_faction_states_from_event(json_data)

            if faction_states:
                await self.repo.replace_faction_states_for_system(faction_states)
                log(f"Replaced {len(faction_states)} faction states from EDDN event")
        except Exception as e:
            log_exception("Error replacing faction states from EDDN event", e)
