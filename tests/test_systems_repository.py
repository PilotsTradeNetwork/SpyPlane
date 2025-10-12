from unittest import IsolatedAsyncioTestCase

from spyplane.database.systems_repository import SystemsRepository
from spyplane.spy_plane import bot


class SystemsRepositoryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await bot.dbinit()
        self.repo = SystemsRepository()
        await self.repo.purge_scout_systems()

    async def test_add_and_remove_systems(self):
        # Test adding systems
        success1 = await self.repo.add_system("Velas", "Primary", "test_user")
        success2 = await self.repo.add_system("Volowahku", "Secondary", "test_user")

        self.assertTrue(success1)
        self.assertTrue(success2)

        # Test getting systems
        systems = await self.repo.get_all_tracked_systems()
        sys_names = [s.system for s in systems]
        self.assertIn("Velas", sys_names)
        self.assertIn("Volowahku", sys_names)

        # Test removing a system
        removed = await self.repo.remove_system("Velas")
        self.assertTrue(removed)

        # Verify it's gone
        systems_after = await self.repo.get_all_tracked_systems()
        sys_names_after = [s.system for s in systems_after]
        self.assertNotIn("Velas", sys_names_after)
        self.assertIn("Volowahku", sys_names_after)

    async def asyncTearDown(self):
        await bot.dbclose()
