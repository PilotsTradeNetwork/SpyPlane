import asyncio
from datetime import datetime, timezone

import httpx
from ptn_utils.logger.logger import get_logger

logger = get_logger("spyplane.services.tick_service")


class TickService:
    def __init__(self, current_tick: int | None = None):
        self.current_tick: int = current_tick or asyncio.run(self.fetch_current_tick())
        logger.info(f"Current Tick: {self.current_tick}")
        if not self.current_tick:
            raise RuntimeError("Failed to fetch current tick on startup")

    def get_current_tick(self) -> datetime:
        return datetime.fromtimestamp(int(self.current_tick), timezone.utc)

    async def has_ticked(self) -> bool:
        try:
            new_tick = await self.fetch_current_tick()
            if not new_tick:
                raise ValueError("fetch_current_tick returned empty value")
        except Exception:
            logger.exception("Error during has_ticked check")
            return False
        tick_changed = self.current_tick != new_tick
        if tick_changed:
            logger.info(f"Tick detected: Current {self.current_tick}, New {new_tick}")
            self.current_tick = new_tick
        else:
            logger.info("No new tick")
        return tick_changed

    @staticmethod
    async def fetch_current_tick() -> int:
        link = "http://tick.infomancer.uk/galtick.json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(link)
            resp.raise_for_status()
            tick_info = resp.json()
        dt = datetime.fromisoformat(tick_info["lastGalaxyTick"].rstrip("Z"))  # python >= 3.11 understands timezone
        dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
