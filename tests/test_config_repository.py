import datetime
from unittest import IsolatedAsyncioTestCase

from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.models.config import Config
from ptn.spyplane.spy_plane import bot


class ConfigRepositoryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await bot.dbinit()
        self.subject = ConfigRepository()

    async def asyncTearDown(self):
        await bot.dbclose()

    async def test_record_scout(self):
        await self.subject.update_config("interval_hours", "6")
        c: Config = await self.subject.get_config("interval_hours")
        await self.assertConfig(c)
        await self.subject.update_config("interval_hours", "4")
        c: Config = await self.subject.get_config("interval_hours")
        await self.assertConfig(c, "4")

    async def assertConfig(self, c, expected="6"):
        self.assertEqual("interval_hours", c.name)
        self.assertEqual(expected, c.value)
        self.assertEqual(
            datetime.datetime.now(datetime.timezone.utc).date(), c.timestamp.date()
        )
