import unittest
from unittest.mock import AsyncMock, MagicMock

from ptn.spyplane.models.scout_system import ScoutSystem
from ptn.spyplane.services.systems_posting_service import SystemsPostingService


def _make_service(
    primary_limit=0,
    secondary_limit=0,
    tertiary_limit=0,
    selection_mode="absolute",
    scouted_1d=None,
    scouted_2d=None,
):
    config_values = {
        "primary_limit": str(primary_limit),
        "secondary_limit": str(secondary_limit),
        "tertiary_limit": str(tertiary_limit),
        "selection_mode": selection_mode,
    }

    async def get_config(name):
        cfg = MagicMock()
        cfg.value = config_values[name]
        return cfg

    config_repo = MagicMock()
    config_repo.get_config = get_config

    history_repo = MagicMock()
    history_repo.get_systems_scouted_since = AsyncMock(
        side_effect=[
            scouted_1d if scouted_1d is not None else [],
            scouted_2d if scouted_2d is not None else [],
        ]
    )

    return SystemsPostingService(repo=None, config_repo=config_repo, history_repo=history_repo)


class SystemsPostingServiceTests(unittest.IsolatedAsyncioTestCase):
    def _primary(self, n=4):
        return [ScoutSystem(f"Primary{i}", "Primary", "test_user", i) for i in range(1, n + 1)]

    def _secondary(self, n=6):
        return [ScoutSystem(f"Secondary{i}", "Secondary", "test_user", i + 10) for i in range(1, n + 1)]

    def _tertiary(self, n=9):
        return [ScoutSystem(f"Tertiary{i}", "Tertiary", "test_user", i + 20) for i in range(1, n + 1)]

    async def test_split_by_priority_no_limits(self):
        primary = self._primary()
        secondary = self._secondary()
        tertiary = self._tertiary()
        systems = primary + secondary + tertiary

        subject = _make_service()
        result = await subject.split_systems_by_priority(systems)

        self.assertEqual(result["Primary"], primary)
        self.assertEqual(result["Secondary"], secondary)
        self.assertEqual(result["Tertiary"], tertiary)

    async def test_split_respects_limits(self):
        primary = self._primary(4)
        secondary = self._secondary(6)
        tertiary = self._tertiary(9)
        systems = primary + secondary + tertiary

        subject = _make_service(primary_limit=2, secondary_limit=3, tertiary_limit=4)
        result = await subject.split_systems_by_priority(systems)

        self.assertEqual(len(result["Primary"]), 2)
        self.assertEqual(len(result["Secondary"]), 3)
        self.assertEqual(len(result["Tertiary"]), 4)
        # Limits take the first N in the sorted order
        self.assertEqual(result["Primary"], primary[:2])
        self.assertEqual(result["Secondary"], secondary[:3])
        self.assertEqual(result["Tertiary"], tertiary[:4])

    async def test_split_zero_limit_means_no_limit(self):
        secondary = self._secondary(6)
        systems = self._primary() + secondary + self._tertiary()

        subject = _make_service(secondary_limit=0)
        result = await subject.split_systems_by_priority(systems)

        self.assertEqual(len(result["Secondary"]), len(secondary))

    async def test_selection_mode_oldest_first(self):
        # Provide systems with non-sequential added_at to confirm sorting
        systems = [
            ScoutSystem("P3", "Primary", "u", 30),
            ScoutSystem("P1", "Primary", "u", 10),
            ScoutSystem("P2", "Primary", "u", 20),
        ]

        subject = _make_service(selection_mode="oldest_first")
        result = await subject.split_systems_by_priority(systems)

        names = [s.system for s in result["Primary"]]
        self.assertEqual(names, ["P1", "P2", "P3"])

    async def test_selection_mode_oldest_first_zero_added_at_sorts_last(self):
        systems = [
            ScoutSystem("P_zero", "Primary", "u", 0),
            ScoutSystem("P1", "Primary", "u", 5),
            ScoutSystem("P2", "Primary", "u", 10),
        ]

        subject = _make_service(selection_mode="oldest_first")
        result = await subject.split_systems_by_priority(systems)

        names = [s.system for s in result["Primary"]]
        self.assertEqual(names[-1], "P_zero")

    async def test_selection_mode_absolute_preserves_order(self):
        systems = [
            ScoutSystem("P3", "Primary", "u", 30),
            ScoutSystem("P1", "Primary", "u", 10),
            ScoutSystem("P2", "Primary", "u", 20),
        ]

        subject = _make_service(selection_mode="absolute")
        result = await subject.split_systems_by_priority(systems)

        names = [s.system for s in result["Primary"]]
        self.assertEqual(names, ["P3", "P1", "P2"])

    async def test_recently_scouted_hidden_from_secondary_and_tertiary(self):
        secondary = self._secondary(4)
        tertiary = self._tertiary(4)
        systems = self._primary() + secondary + tertiary

        # secondary[0] scouted within 1d, tertiary[0] scouted within 2d
        subject = _make_service(
            scouted_1d=[secondary[0].system],
            scouted_2d=[tertiary[0].system],
        )
        result = await subject.split_systems_by_priority(systems)

        self.assertNotIn(secondary[0], result["Secondary"])
        self.assertIn(secondary[1], result["Secondary"])
        self.assertNotIn(tertiary[0], result["Tertiary"])
        self.assertIn(tertiary[1], result["Tertiary"])

    async def test_primary_not_filtered_by_scouted(self):
        primary = self._primary(3)
        systems = primary

        subject = _make_service(scouted_1d=[primary[0].system], scouted_2d=[primary[1].system])
        result = await subject.split_systems_by_priority(systems)

        # Primary is never filtered by scout history
        self.assertEqual(result["Primary"], primary)
