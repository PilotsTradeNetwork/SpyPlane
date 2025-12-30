import asyncio

from discord.ext import tasks

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.services.daily_faction_state_service import DailyFactionStateService
from ptn.spyplane.services.systems_posting_service import SystemsPostingService
from ptn.spyplane.services.tick_service import TickService


class PostAfterTickService:
    def __init__(
        self,
        systems=None,
        repo=None,
        ticks=None,
        daily=None,
    ):
        self.systems: SystemsPostingService = systems or SystemsPostingService()
        self.repo: ConfigRepository = repo or ConfigRepository()
        self.tick_service: TickService = ticks or TickService()
        self.daily: DailyFactionStateService = daily or DailyFactionStateService()

    async def post_report(self):
        log("Put up report")
        await self.daily.notify_daily_news()

    async def post_systems(self):
        log("Posting systems now")
        await self.systems.publish_systems_to_scout()

    async def run_after_interval(
        self, pre_launch_message: bool, interval_config_key: str, method_to_run
    ):
        try:
            hours = await ConfigRepository().get_config(interval_config_key)
            message = f"Tick detected. Spy Plane will take off in ~ {hours.value} hours"
            log(message)
            if pre_launch_message:
                bot = get_bot()
                await bot.channel.send(message)
            seconds = int(hours.value) * 3600
            log(f"Waiting for {seconds} seconds")
            await asyncio.sleep(seconds)
            await method_to_run()
        except Exception as e:
            log_exception("run_after_interval", e)

    @tasks.loop(minutes=5)
    async def tick_check_and_schedule(self):
        has_ticked = await self.tick_service.has_ticked()
        if has_ticked:
            self.on_tick()

    def on_tick(self):
        asyncio.create_task(
            self.run_after_interval(True, "interval_hours", self.post_systems)
        )
        asyncio.create_task(
            self.run_after_interval(False, "daily_interval_hours", self.post_report)
        )
