from typing import List

from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.database.faction_states_repository import FactionStatesRepository


class FactionStateService:
    """Service to extract and store faction state data from EDDN events"""

    def __init__(self, repo=None):
        self.repo: FactionStatesRepository = repo or FactionStatesRepository()

    @staticmethod
    def _extract_states(state_list: List) -> str:
        """Extract state names from a list of state objects or strings"""
        states = [
            state_obj.get("State") if isinstance(state_obj, dict) else state_obj
            for state_obj in state_list
            if state_obj and (state_obj.get("State") if isinstance(state_obj, dict) else state_obj)
        ]
        return ",".join(states)

    def extract_faction_states_from_event(self, json_data: dict) -> List[dict]:
        try:
            message = json_data.get("message", {})
            star_system = message.get("StarSystem")
            
            if not star_system:
                log("EDDN event missing StarSystem field for faction state extraction")
                return []
            
            return [
                {
                    "system": star_system,
                    "faction": faction.get("Name"),
                    "active_csv": self._extract_states(faction.get("ActiveStates", [])),
                    "pending_csv": self._extract_states(faction.get("PendingStates", [])),
                }
                for faction in message.get("Factions", [])
                if faction.get("Name")
            ]
        except Exception as e:
            log_exception("Error extracting faction states from EDDN event", e)
            return []

    async def upsert_faction_states_from_event(self, json_data: dict) -> None:
        try:
            faction_states = self.extract_faction_states_from_event(json_data)
            
            for state_data in faction_states:
                await self.repo.upsert_faction_state(**state_data)
            
            if faction_states:
                log(f"Upserted {len(faction_states)} faction states from EDDN event")
        except Exception as e:
            log_exception("Error upserting faction states from EDDN event", e)

