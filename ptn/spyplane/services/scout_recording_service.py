from datetime import UTC, datetime

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository


class ScoutRecordingService:
    def __init__(self, systems_repo=None, history_repo=None, config_repo=None):
        self.systems_repo = systems_repo or SystemsRepository()
        self.history_repo = history_repo or ScoutHistoryRepository()
        self.config_repo = config_repo or ConfigRepository()

    async def record_reaction(self, content: str, username: str, userid: int) -> None:
        try:
            bot = get_bot()
            log(f"Content: {content}")
            system = await self.systems_repo.get_system(content)
            last_posted_at = int((await self.config_repo.get_config("last_posted_at")).value)
            async with bot.lock:
                await self.systems_repo.begin()
                ts = datetime.now(UTC)
                inserted = await self.history_repo.record_scout(system, username, userid, ts, since_ts=last_posted_at)
                if inserted:
                    await self.systems_repo.mark_scouted(system.system)
                await self.systems_repo.commit()
                if inserted:
                    log(f"Scout recorded: {username} scouted {system.system}")
                else:
                    log(f"Duplicate scout ignored: {system.system} already recorded this tick")
        except Exception as e:
            log("OnReaction: Error when recording the scout")
            log(str(e))
