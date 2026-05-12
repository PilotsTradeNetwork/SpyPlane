import asyncio
from datetime import UTC, datetime

import httpx

from ptn.spyplane.constants import log


class TickService:
    def __init__(self, current_tick: int | None = None):
        self.current_tick: int = current_tick or asyncio.run(self.fetch_current_tick())
        log(f"Current Tick: {self.current_tick}")
        if not self.current_tick:
            raise RuntimeError("Failed to fetch current tick on startup")

    def get_current_tick(self) -> datetime:
        return datetime.fromtimestamp(int(self.current_tick), UTC)

    async def has_ticked(self) -> bool:
        try:
            new_tick = await self.fetch_current_tick()
            if not new_tick:
                raise ValueError("fetch_current_tick returned empty value")
        except Exception as e:
            log(f"Error during has_ticked check: {e}")
            return False
        tick_changed = self.current_tick != new_tick
        if tick_changed:
            log(f"Tick detected: Current {self.current_tick}, New {new_tick}")
            self.current_tick = new_tick
        else:
            log("No new tick")
        return tick_changed

    @staticmethod
    async def fetch_current_tick() -> int:
        link = "http://tick.infomancer.uk/galtick.json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(link)
            resp.raise_for_status()
            tick_info = resp.json()
        dt = datetime.fromisoformat(tick_info["lastGalaxyTick"].rstrip("Z"))  # python >= 3.11 understands timezone
        dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp())
