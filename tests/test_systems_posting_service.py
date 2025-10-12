import unittest

from spyplane.services.systems_posting_service import SystemsPostingService
from spyplane.models.scout_system import ScoutSystem


class SystemsPostingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.subject = SystemsPostingService(None)

    def tearDown(self) -> None:
        pass

    def test_split_systems_by_priority(self):
        primary = [
            ScoutSystem(f"System{i}", "Primary", "test_user", 1) for i in range(1, 5)
        ]
        secondary: list[ScoutSystem] = [
            ScoutSystem(f"System{i}", "Secondary", "test_user", 1) for i in range(6, 12)
        ]
        tertiary = [
            ScoutSystem(f"System{i}", "Tertiary", "test_user", 1) for i in range(12, 21)
        ]
        carryover = []
        systems = primary + secondary + tertiary
        day_list = self.subject.split_systems_by_priority(systems, carryover)

        # Test that systems are correctly split by priority
        self.assertEqual(day_list["Primary"], primary)
        self.assertEqual(day_list["Secondary"], secondary)
        self.assertEqual(day_list["Tertiary"], tertiary)

        # Test with carryover systems
        carryover_secondary = [
            ScoutSystem("CarryoverSecondary", "Secondary", "test_user", 1)
        ]
        carryover_tertiary = [
            ScoutSystem("CarryoverTertiary", "Tertiary", "test_user", 1)
        ]
        carryover = carryover_secondary + carryover_tertiary

        day_list_with_carryover = self.subject.split_systems_by_priority(
            systems, carryover
        )

        # Check that carryover systems are added
        self.assertEqual(len(day_list_with_carryover["Secondary"]), len(secondary) + 1)
        self.assertEqual(len(day_list_with_carryover["Tertiary"]), len(tertiary) + 1)
        self.assertIn(carryover_secondary[0], day_list_with_carryover["Secondary"])
        self.assertIn(carryover_tertiary[0], day_list_with_carryover["Tertiary"])
