from datetime import datetime
from ptn.spyplane.constants import log
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.spy_plane import bot


class ScoutRecordingService:
    def __init__(
        self, systems_repo=SystemsRepository(), history_repo=ScoutHistoryRepository()
    ):
        self.systems_repo = systems_repo
        self.history_repo = history_repo

    async def record_reaction(self, content: str, username: str, userid: int) -> None:
        try:
            log(f"Content: {content}")
            system = await self.systems_repo.get_system(content)
            async with bot.lock:
                await self.systems_repo.begin()
                ts = datetime.now()
                await self.history_repo.record_scout(system, username, userid, ts)
                await self.systems_repo.remove_scouted(system.system)
                await self.systems_repo.commit()
                log(f"Message deleted: {content}")
                log(f"Scout recorded: {username} scouted {system.system}")
        except Exception as e:
            log("OnReaction: Error when recording the scout")
            log(str(e))
