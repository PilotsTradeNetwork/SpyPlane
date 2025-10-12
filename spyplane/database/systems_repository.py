from datetime import datetime

from spyplane.constants import log
from spyplane.database.base_repository import BaseRepository
from spyplane.models.scout_system import ScoutSystem

insert_scout_system = """
insert into scout_systems (system_name, priority, added_by, added_at) values (?,?,?,?);
"""
insert_post_system = """
insert or ignore into scout_systems_posted (system_name, priority) values (?,?);
"""
update_post_system = """
update scout_systems_posted set priority=? where system_name=?;
"""
select_scout_system = """
select *
from scout_systems
where system_name=?;
"""


get_is_valid_system_query = """
select name
from systems
where name = ?
"""

remove_scouted_system = """
delete from scout_systems_posted where system_name=?
"""

purge_scout = """
delete from scout_systems
"""

purge_posted = """
delete from scout_systems_posted
"""

get_post_systems = """
select s.system_name, s.priority
from scout_systems_posted s
"""


class SystemsRepository(BaseRepository):
    async def is_valid_system(self, system: str) -> bool:
        async with self.db().execute(get_is_valid_system_query, [system]) as cur:
            row = await cur.fetchone()
            return row and row[0] and row[0] == system

    async def get_carryover_systems(self) -> list[ScoutSystem]:
        return await self.get_systems(get_post_systems)

    async def get_system(self, system_name) -> ScoutSystem:
        async with self.db().execute(select_scout_system, [system_name]) as cur:
            row = await cur.fetchone()
        return ScoutSystem(row[0], row[1], row[2], row[3])

    async def purge_scout_systems(self) -> None:
        await self.db().execute(purge_scout)

    async def purge_posted_systems(self) -> None:
        await self.begin()
        await self.db().execute(purge_posted)
        await self.commit()

    async def remove_scouted(self, system_name) -> None:
        await self.db().execute(remove_scouted_system, [system_name])
        log(f"Removed scout: {system_name}")

    async def get_systems(self, query) -> list[ScoutSystem]:
        async with self.db().execute(query) as cur:
            rows = await cur.fetchall()
        # Handle different query result formats
        if (
            len(rows) > 0 and len(rows[0]) == 4
        ):  # scout_systems table (system_name, priority, added_by, added_at)
            return [ScoutSystem(row[0], row[1], row[2], row[3]) for row in rows]
        elif (
            len(rows) > 0 and len(rows[0]) == 2
        ):  # scout_systems_posted table (system_name, priority)
            return [ScoutSystem(row[0], row[1], "posted", 0) for row in rows]
        else:
            return []

    async def write_system_to_post(self, systems_to_scout: list[ScoutSystem]):
        await self.begin()
        array_of_tuples = [
            (system.system, system.priority) for system in systems_to_scout
        ]
        array_of_tuples_update = [
            (system.priority, system.system) for system in systems_to_scout
        ]
        await self.db().executemany(insert_post_system, array_of_tuples)
        await self.db().executemany(update_post_system, array_of_tuples_update)
        await self.commit()

    async def write_system_to_scout(self, systems_to_scout: list[ScoutSystem]):
        systems_to_write = self.remove_duplicates(systems_to_scout)
        await self.begin()
        await self.purge_scout_systems()
        array_of_tuples = [
            (system.system, system.priority, system.added_by, system.added_at)
            for system in systems_to_write
        ]
        await self.db().executemany(insert_scout_system, array_of_tuples)
        await self.commit()

    async def add_system(self, system_name: str, priority: str, added_by: str) -> bool:
        """Add a system to track. Returns True if added, False if already exists."""
        try:
            await self.db().execute(
                insert_scout_system,
                [system_name, priority, added_by, int(datetime.now().timestamp())],
            )
            await self.commit()
            return True
        except Exception as e:
            log(f"Error adding system {system_name}: {e}")
            return False

    async def remove_system(self, system_name: str) -> bool:
        """Remove a system from tracking. Returns True if removed, False if not found."""
        try:
            cursor = await self.db().execute(
                "DELETE FROM scout_systems WHERE system_name = ?", [system_name]
            )
            await self.commit()
            return cursor.rowcount > 0
        except Exception as e:
            log(f"Error removing system {system_name}: {e}")
            return False

    async def get_all_tracked_systems(self) -> list[ScoutSystem]:
        """Get all tracked systems regardless of validity."""
        query = "SELECT system_name, priority, added_by, added_at FROM scout_systems ORDER BY added_at"
        return await self.get_systems(query)

    @staticmethod
    def remove_duplicates(systems_to_scout):
        sys_names, systems_to_write = [], []
        for sys in systems_to_scout:
            if sys.system not in sys_names:
                systems_to_write.append(sys)
                sys_names.append(sys.system)
        return systems_to_write
