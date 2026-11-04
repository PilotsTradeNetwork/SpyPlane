from datetime import UTC, datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import httpx

from ptn.spyplane.services.post_after_tick_service import PostAfterTickService

TICK_URL = "http://tick.infomancer.uk/galtick.json"
FIXED_TICK = 1_700_000_000  # 2023-11-14T22:13:20Z


def tick_response(last_galaxy_tick: str) -> httpx.Response:
    return httpx.Response(200, json={"lastGalaxyTick": last_galaxy_tick}, request=httpx.Request("GET", TICK_URL))


class PostAfterTickServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.http_get = AsyncMock(return_value=tick_response("2023-11-14T22:13:20.000Z"))
        patcher = patch.object(httpx.AsyncClient, "get", new=self.http_get)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.subject = PostAfterTickService(None)

    async def test_tick_unchanged(self):
        tick_check = await self.subject.tick_check_and_schedule()
        self.assertFalse(tick_check)
        self.assertEqual(FIXED_TICK, self.subject.tick_service.current_tick)
        self.assertTrue(self.subject.tick_service.get_current_tick() <= datetime.now(UTC))
        self.http_get.assert_awaited_with(TICK_URL)

    async def test_tick_changed(self):
        self.http_get.return_value = tick_response("2023-11-15T22:13:20.000Z")
        self.assertTrue(await self.subject.tick_service.has_ticked())
        self.assertEqual(FIXED_TICK + 86_400, self.subject.tick_service.current_tick)
