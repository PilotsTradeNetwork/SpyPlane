from datetime import datetime, timezone
from typing import List
from unittest import IsolatedAsyncioTestCase

from spyplane.database.scout_history_repository import ScoutHistoryRepository
from spyplane.models.scout_history import ScoutHistory
from spyplane.models.scout_system import ScoutSystem
from spyplane.spy_plane import bot


class ScoutHistoryRepositoryTests(IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        await bot.dbinit()
        self.subject = ScoutHistoryRepository()
        await self.subject.purge_scout_systems_history()

    async def asyncTearDown(self):
        await bot.dbclose()

    async def test_record_scout(self):
        await self.subject.record_scout(ScoutSystem('Volowahku', '1', 3), "zaszrespawned", 354990093980663889, datetime.now())
        history: List[ScoutHistory] = await self.subject.get_history(username="zaszrespawned")
        for scout in history:
            print(scout)
        self.assertEqual(len(history), 1)
        self.assertEqual("Volowahku", history[0].system_name)
        self.assertEqual("zaszrespawned", history[0].username)
        self.assertEqual(354990093980663889, history[0].userid)
        self.assertEqual(datetime.now(timezone.utc).date(), history[0].timestamp.date())
