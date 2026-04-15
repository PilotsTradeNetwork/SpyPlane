from datetime import datetime, timezone

from ptn_utils.logger.logger import get_logger

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository

logger = get_logger("spyplane.services.scout_recording_service")


class ScoutRecordingService:
    def __init__(self, systems_repo=None, history_repo=None):
        self.systems_repo = systems_repo or SystemsRepository()
        self.history_repo = history_repo or ScoutHistoryRepository()

    async def record_reaction(self, content: str, username: str, userid: int) -> None:
        try:
            bot = get_bot()
            logger.info(f"Content: {content}")
            system = await self.systems_repo.get_system(content)
            async with bot.lock:
                await self.systems_repo.begin()
                ts = datetime.now(timezone.utc)
                await self.history_repo.record_scout(system, username, userid, ts)
                await self.systems_repo.remove_scouted(system.system)
                await self.systems_repo.commit()
                logger.info(f"Message deleted: {content}")
                logger.info(f"Scout recorded: {username} scouted {system.system}")
        except Exception:
            logger.exception("OnReaction: Error when recording the scout")
