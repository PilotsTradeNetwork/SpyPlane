import time
from datetime import datetime, timezone

from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository
from ptn.spyplane.models.scout_history import ScoutHistory
from ptn.spyplane.models.scout_system import ScoutSystem

insert_scout_history = """
insert into scout_history (system_name, username, userid, timestamp) values (?,?,?,?);
"""

read_scout_history = """
select id, system_name, username, userid, timestamp from scout_history where 1=1
"""

purge_scout_history = """
delete from scout_history
"""

recently_scouted_systems = """
select distinct system_name from scout_history where timestamp >= ?
"""


class ScoutHistoryRepository(BaseRepository):
    async def record_scout(self, system: ScoutSystem, username, userid, ts=None):
        if ts is None:
            ts = datetime.now(timezone.utc)
        await self.db().execute(
            insert_scout_history,
            (system.system, username, userid, time.mktime(ts.timetuple())),
        )
        log(f"Added history: {system.system}, {username}, {userid}, {ts}")

    async def get_history(
        self,
        system: str | None = None,
        username: str | None = None,
        userid: int | None = None,
    ):
        params = []
        query = read_scout_history
        if system is not None:
            query += " and system_name=?"
            params.append(system)
        if username is not None:
            query += " and username=?"
            params.append(username)
        if userid is not None:
            query += " and userid=?"
            params.append(userid)
        async with self.db().execute(query, parameters=params) as cur:
            rows = await cur.fetchall()
            return [ScoutHistory(r[0], r[1], r[2], r[3], datetime.fromtimestamp(r[4], timezone.utc)) for r in rows]

    async def get_systems_scouted_since(self, cutoff: float) -> set[str]:
        """Return the set of system names that have a scout record at or after cutoff (UTC timestamp)."""
        async with self.db().execute(recently_scouted_systems, parameters=[cutoff]) as cur:
            rows = await cur.fetchall()
            return {r[0] for r in rows}

    async def purge_scout_systems_history(self) -> None:
        await self.db().execute(purge_scout_history)
