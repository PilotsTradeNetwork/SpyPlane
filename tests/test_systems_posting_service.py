import unittest

from ptn.spyplane.services.systems_posting_service import SystemsPostingService
from ptn.spyplane.models.scout_system import ScoutSystem


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
        daily_sequence = 0
        day_list = self.subject.split_systems_by_priority(systems, daily_sequence, carryover)

        # Test that systems are correctly split by priority
        # Primary should always include all systems
        self.assertEqual(day_list["Primary"], primary)
        # Secondary and Tertiary are rotated, so we check that they contain a subset
        # Secondary is split into 2 groups, so we should get approximately half
        self.assertGreater(len(day_list["Secondary"]), 0)
        self.assertLessEqual(len(day_list["Secondary"]), len(secondary))
        # Tertiary is split into 3 groups, so we should get approximately one third
        self.assertGreater(len(day_list["Tertiary"]), 0)
        self.assertLessEqual(len(day_list["Tertiary"]), len(tertiary))
        # All returned systems should be from the original lists
        self.assertTrue(all(s in secondary for s in day_list["Secondary"]))
        self.assertTrue(all(s in tertiary for s in day_list["Tertiary"]))

        # Test with carryover systems
        carryover_secondary = [
            ScoutSystem("CarryoverSecondary", "Secondary", "test_user", 1)
        ]
        carryover_tertiary = [
            ScoutSystem("CarryoverTertiary", "Tertiary", "test_user", 1)
        ]
        carryover = carryover_secondary + carryover_tertiary

        day_list_with_carryover = self.subject.split_systems_by_priority(
            systems, daily_sequence, carryover
        )

        # Check that carryover systems are added (if not already in the rotated list)
        # The carryover should be added if it's not already in the list
        secondary_count_before_carryover = len(day_list["Secondary"])
        tertiary_count_before_carryover = len(day_list["Tertiary"])
        # Carryover will only be added if not already present
        self.assertGreaterEqual(
            len(day_list_with_carryover["Secondary"]), secondary_count_before_carryover
        )
        self.assertGreaterEqual(
            len(day_list_with_carryover["Tertiary"]), tertiary_count_before_carryover
        )
        # Check that carryover systems are included
        self.assertIn(carryover_secondary[0], day_list_with_carryover["Secondary"])
        self.assertIn(carryover_tertiary[0], day_list_with_carryover["Tertiary"])
