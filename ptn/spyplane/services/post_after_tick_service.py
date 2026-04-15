import asyncio

from discord.ext import tasks
from ptn_utils.logger.logger import get_logger

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.services.daily_faction_state_service import DailyFactionStateService
from ptn.spyplane.services.systems_posting_service import SystemsPostingService
from ptn.spyplane.services.tick_service import TickService

logger = get_logger("spyplane.services.post_after_tick_service")


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
        logger.info("Put up report")
        await self.daily.notify_daily_news()

    async def post_systems(self):
        logger.info("Posting systems now")
        await self.systems.publish_systems_to_scout()

    async def run_after_interval(self, pre_launch_message: bool, interval_config_key: str, method_to_run):
        try:
            hours = await ConfigRepository().get_config(interval_config_key)
            message = f"Tick detected. Spy Plane will take off in ~ {hours.value} hours"
            logger.info(message)
            if pre_launch_message:
                bot = get_bot()
                await bot.channel.send(message)
            seconds = int(hours.value) * 3600
            logger.info(f"Waiting for {seconds} seconds")
            await asyncio.sleep(seconds)
            await method_to_run()
        except Exception:
            logger.exception("Exception in run_after_interval")

    @tasks.loop(minutes=5)
    async def tick_check_and_schedule(self):
        has_ticked = await self.tick_service.has_ticked()
        if has_ticked:
            self.on_tick()

    def on_tick(self):
        asyncio.create_task(self.run_after_interval(True, "interval_hours", self.post_systems))  # noqa: RUF006
        asyncio.create_task(self.run_after_interval(False, "daily_interval_hours", self.post_report))  # noqa: RUF006
