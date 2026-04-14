from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from ptn.spyplane.services.faction_state_service import FactionStateService


class FactionStateServiceTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = FactionStateService()

    def test_extract_states_with_dict_objects(self):
        state_list = [{"State": "Boom"}, {"State": "Expansion"}]
        result = FactionStateService._extract_states(state_list)
        self.assertEqual(result, "Boom,Expansion")

    def test_extract_states_with_strings(self):
        state_list = ["Boom", "Expansion"]
        result = FactionStateService._extract_states(state_list)
        self.assertEqual(result, "Boom,Expansion")

    def test_extract_states_mixed_types(self):
        state_list = [{"State": "Boom"}, "Expansion"]
        result = FactionStateService._extract_states(state_list)
        self.assertEqual(result, "Boom,Expansion")

    def test_extract_states_empty_list(self):
        result = FactionStateService._extract_states([])
        self.assertEqual(result, "")

    def test_extract_states_with_none_values(self):
        state_list = [{"State": "Boom"}, None, {"State": None}, ""]
        result = FactionStateService._extract_states(state_list)
        self.assertEqual(result, "Boom")

    def test_extract_faction_states_from_event_basic(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "SystemFaction": {"Name": "TestFaction"},
                "Factions": [
                    {
                        "Name": "TestFaction",
                        "ActiveStates": [{"State": "Boom"}],
                        "PendingStates": [{"State": "Expansion"}],
                        "Influence": 0.5,
                    }
                ],
            }
        }
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["system"], "TestSystem")
        self.assertEqual(result[0]["faction"], "TestFaction")
        self.assertEqual(result[0]["active_csv"], "Boom")
        self.assertEqual(result[0]["pending_csv"], "Expansion")
        self.assertEqual(result[0]["influence"], 0.5)
        self.assertEqual(result[0]["controlling"], 1)

    def test_extract_faction_states_from_event_multiple_factions(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "SystemFaction": {"Name": "Faction1"},
                "Factions": [
                    {"Name": "Faction1", "ActiveStates": [{"State": "Boom"}], "PendingStates": [], "Influence": 0.6},
                    {"Name": "Faction2", "ActiveStates": [], "PendingStates": [{"State": "War"}], "Influence": 0.4},
                ],
            }
        }
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["faction"], "Faction1")
        self.assertEqual(result[0]["active_csv"], "Boom")
        self.assertEqual(result[0]["pending_csv"], "")
        self.assertEqual(result[0]["influence"], 0.6)
        self.assertEqual(result[0]["controlling"], 1)
        self.assertEqual(result[1]["faction"], "Faction2")
        self.assertEqual(result[1]["active_csv"], "")
        self.assertEqual(result[1]["pending_csv"], "War")
        self.assertEqual(result[1]["influence"], 0.4)
        self.assertEqual(result[1]["controlling"], 0)

    def test_extract_faction_states_from_event_multiple_active_states(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "Factions": [
                    {
                        "Name": "TestFaction",
                        "ActiveStates": [{"State": "Boom"}, {"State": "Expansion"}],
                        "PendingStates": [],
                    }
                ],
            }
        }
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result[0]["active_csv"], "Boom,Expansion")

    def test_extract_faction_states_from_event_no_states(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "Factions": [{"Name": "TestFaction", "ActiveStates": [], "PendingStates": []}],
            }
        }
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["active_csv"], "")
        self.assertEqual(result[0]["pending_csv"], "")

    def test_extract_faction_states_from_event_missing_starsystem(self):
        event = {"message": {"Factions": [{"Name": "TestFaction", "ActiveStates": [{"State": "Boom"}]}]}}
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result, [])

    def test_extract_faction_states_from_event_missing_factions(self):
        event = {"message": {"StarSystem": "TestSystem"}}
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result, [])

    def test_extract_faction_states_from_event_empty_factions(self):
        event = {"message": {"StarSystem": "TestSystem", "Factions": []}}
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result, [])

    def test_extract_faction_states_from_event_faction_without_name(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "Factions": [
                    {"ActiveStates": [{"State": "Boom"}]},
                    {"Name": "ValidFaction", "ActiveStates": [{"State": "Expansion"}]},
                ],
            }
        }
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["faction"], "ValidFaction")

    def test_extract_faction_states_from_event_missing_message(self):
        event = {}
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result, [])

    def test_extract_faction_states_from_event_invalid_structure(self):
        event = {"invalid": "data"}
        result = self.service.extract_faction_states_from_event(event)
        self.assertEqual(result, [])

    async def test_replace_faction_states_from_event_success(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "SystemFaction": {"Name": "TestFaction"},
                "Factions": [
                    {
                        "Name": "TestFaction",
                        "ActiveStates": [{"State": "Boom"}],
                        "PendingStates": [{"State": "Expansion"}],
                        "Influence": 0.5,
                    }
                ],
            }
        }

        mock_repo = AsyncMock()
        service = FactionStateService(repo=mock_repo)

        await service.replace_faction_states_from_event(event)

        mock_repo.replace_faction_states_for_system.assert_called_once()
        call_args = mock_repo.replace_faction_states_for_system.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]["system"], "TestSystem")
        self.assertEqual(call_args[0]["faction"], "TestFaction")
        self.assertEqual(call_args[0]["active_csv"], "Boom")
        self.assertEqual(call_args[0]["pending_csv"], "Expansion")
        self.assertEqual(call_args[0]["influence"], 0.5)
        self.assertEqual(call_args[0]["controlling"], 1)

    async def test_replace_faction_states_from_event_multiple_factions(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "SystemFaction": {"Name": "Faction1"},
                "Factions": [
                    {"Name": "Faction1", "ActiveStates": [{"State": "Boom"}], "PendingStates": [], "Influence": 0.6},
                    {"Name": "Faction2", "ActiveStates": [], "PendingStates": [{"State": "War"}], "Influence": 0.4},
                ],
            }
        }

        mock_repo = AsyncMock()
        service = FactionStateService(repo=mock_repo)

        await service.replace_faction_states_from_event(event)

        mock_repo.replace_faction_states_for_system.assert_called_once()
        call_args = mock_repo.replace_faction_states_for_system.call_args[0][0]
        self.assertEqual(len(call_args), 2)
        self.assertEqual(call_args[0]["faction"], "Faction1")
        self.assertEqual(call_args[1]["faction"], "Faction2")

    async def test_replace_faction_states_from_event_empty_result(self):
        event = {"message": {"StarSystem": "TestSystem", "Factions": []}}

        mock_repo = AsyncMock()
        service = FactionStateService(repo=mock_repo)

        await service.replace_faction_states_from_event(event)

        mock_repo.replace_faction_states_for_system.assert_not_called()

    async def test_replace_faction_states_from_event_repository_error(self):
        event = {
            "message": {
                "StarSystem": "TestSystem",
                "SystemFaction": {"Name": "TestFaction"},
                "Factions": [{"Name": "TestFaction", "ActiveStates": [{"State": "Boom"}], "Influence": 0.5}],
            }
        }

        mock_repo = AsyncMock()
        mock_repo.replace_faction_states_for_system.side_effect = Exception("Database error")
        service = FactionStateService(repo=mock_repo)

        # Should not raise, but log the error
        await service.replace_faction_states_from_event(event)

        mock_repo.replace_faction_states_for_system.assert_called_once()
