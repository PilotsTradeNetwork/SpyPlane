from unittest import IsolatedAsyncioTestCase

from ptn.spyplane.database.faction_states_repository import FactionStatesRepository
from ptn.spyplane.spy_plane import bot


class FactionStatesRepositoryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await bot.dbinit()
        self.repo = FactionStatesRepository()
        # Clean up any existing test data
        await self._cleanup_test_data()

    async def _cleanup_test_data(self):
        """Helper to clean up test data"""
        try:
            await self.repo.delete_faction_state("TestSystem", "TestFaction")
        except:
            pass
        try:
            await self.repo.delete_faction_state("TestSystem", "TestFaction2")
        except:
            pass
        try:
            await self.repo.delete_faction_state("TestSystem2", "TestFaction")
        except:
            pass

    async def test_upsert_faction_state_insert(self):
        """Test inserting a new faction state"""
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "boom,expansion", "war"
        )
        
        result = await self.repo.get_faction_state("TestSystem", "TestFaction")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "TestSystem")
        self.assertEqual(result[1], "TestFaction")
        self.assertEqual(result[2], "boom,expansion")
        self.assertEqual(result[3], "war")

    async def test_upsert_faction_state_update(self):
        """Test updating an existing faction state"""
        # Insert first
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "boom", "war"
        )
        
        # Update it
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "expansion,boom", "civil_war"
        )
        
        result = await self.repo.get_faction_state("TestSystem", "TestFaction")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], "expansion,boom")
        self.assertEqual(result[3], "civil_war")

    async def test_get_faction_state_not_found(self):
        """Test getting a non-existent faction state"""
        result = await self.repo.get_faction_state("NonExistent", "NonExistent")
        self.assertIsNone(result)

    async def test_get_all_faction_states_for_system(self):
        """Test getting all faction states for a system"""
        # Insert multiple factions for the same system
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "boom", "war"
        )
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction2", "expansion", "civil_war"
        )
        # Insert a faction for a different system
        await self.repo.upsert_faction_state(
            "TestSystem2", "TestFaction", "boom", "war"
        )
        
        results = await self.repo.get_all_faction_states_for_system("TestSystem")
        self.assertEqual(len(results), 2)
        
        # Check that both factions are present
        faction_names = [r[1] for r in results]
        self.assertIn("TestFaction", faction_names)
        self.assertIn("TestFaction2", faction_names)
        
        # Verify no results from other system
        for result in results:
            self.assertEqual(result[0], "TestSystem")

    async def test_get_all_faction_states_for_system_empty(self):
        """Test getting faction states for a system with none"""
        results = await self.repo.get_all_faction_states_for_system("EmptySystem")
        self.assertEqual(len(results), 0)

    async def test_delete_faction_state(self):
        """Test deleting a faction state"""
        # Insert first
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "boom", "war"
        )
        
        # Verify it exists
        result = await self.repo.get_faction_state("TestSystem", "TestFaction")
        self.assertIsNotNone(result)
        
        # Delete it
        await self.repo.delete_faction_state("TestSystem", "TestFaction")
        
        # Verify it's gone
        result = await self.repo.get_faction_state("TestSystem", "TestFaction")
        self.assertIsNone(result)

    async def test_composite_key_uniqueness(self):
        """Test that the composite key (system, faction) works correctly"""
        # Insert same faction in different systems
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "boom", "war"
        )
        await self.repo.upsert_faction_state(
            "TestSystem2", "TestFaction", "expansion", "civil_war"
        )
        
        # Both should exist independently
        result1 = await self.repo.get_faction_state("TestSystem", "TestFaction")
        result2 = await self.repo.get_faction_state("TestSystem2", "TestFaction")
        
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertEqual(result1[2], "boom")
        self.assertEqual(result2[2], "expansion")

    async def test_empty_csv_values(self):
        """Test that empty CSV strings are handled correctly"""
        await self.repo.upsert_faction_state(
            "TestSystem", "TestFaction", "", ""
        )
        
        result = await self.repo.get_faction_state("TestSystem", "TestFaction")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], "")
        self.assertEqual(result[3], "")

    async def asyncTearDown(self):
        await self._cleanup_test_data()
        await bot.dbclose()

