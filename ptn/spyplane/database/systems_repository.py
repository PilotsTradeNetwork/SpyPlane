from datetime import datetime

from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository
from ptn.spyplane.models.scout_system import ScoutSystem
from ptn.spyplane.services.scout_systems_cache import ScoutSystemsCache

insert_scout_system = """
insert into scout_systems (system_name, priority, added_by, added_at) values (?,?,?,?);
"""
insert_post_system = """
insert or ignore into scout_systems_posted (system_name, priority, message_id) values (?,?,?);
"""
update_post_system = """
update scout_systems_posted set priority=?, message_id=? where system_name=?;
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

get_message_id_query = """
select message_id
from scout_systems_posted
where system_name = ?
"""

# Cache instance
_scout_cache = ScoutSystemsCache()


class SystemsRepository(BaseRepository):
    async def is_valid_system(self, system: str) -> bool:
        async with self.db().execute(get_is_valid_system_query, [system]) as cur:
            row = await cur.fetchone()
            return row and row[0] and row[0] == system

    async def get_carryover_systems(self) -> list[ScoutSystem]:
        return await self.get_systems(get_post_systems)

    async def get_message_id(self, system_name: str) -> int | None:
        """Get message_id for a system from scout_systems_posted table"""
        async with self.db().execute(get_message_id_query, [system_name]) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else None

    async def get_system(self, system_name) -> ScoutSystem:
        async with self.db().execute(select_scout_system, [system_name]) as cur:
            row = await cur.fetchone()
        return ScoutSystem(row[0], row[1], row[2], row[3])

    async def purge_scout_systems(self) -> None:
        await self.db().execute(purge_scout)
        # Clear cache when purging
        _scout_cache.clear()

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

    async def write_system_to_post(
        self, systems_to_scout: list[ScoutSystem], message_ids: dict[str, int] | None = None
    ):
        """
        Write systems to scout_systems_posted table with optional message IDs
        
        Args:
            systems_to_scout: List of ScoutSystem objects to write
            message_ids: Optional dict mapping system_name to message_id
        """
        await self.begin()
        # Prepare insert tuples with message_id (None if not provided)
        array_of_tuples = [
            (
                system.system,
                system.priority,
                message_ids.get(system.system) if message_ids else None,
            )
            for system in systems_to_scout
        ]
        # Prepare update tuples with message_id
        array_of_tuples_update = [
            (
                system.priority,
                message_ids.get(system.system) if message_ids else None,
                system.system,
            )
            for system in systems_to_scout
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
        # Update cache
        _scout_cache.load(systems_to_write)

    async def add_system(self, system_name: str, priority: str, added_by: str) -> bool:
        """Add a system to track. Returns True if added, False if already exists."""
        try:
            added_at = int(datetime.now().timestamp())
            await self.db().execute(
                insert_scout_system,
                [system_name, priority, added_by, added_at],
            )
            await self.commit()

            # Update cache
            system = ScoutSystem(system_name, priority, added_by, added_at)
            _scout_cache.add(system)

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

            if cursor.rowcount > 0:
                # Update cache
                _scout_cache.remove(system_name)
                return True
            return False
        except Exception as e:
            log(f"Error removing system {system_name}: {e}")
            return False

    async def get_all_tracked_systems(self, force_reload: bool = False) -> list[ScoutSystem]:
        """
        Get all tracked systems from cache if available, otherwise from DB
        Args:
            force_reload: If True, reload from database even if cache exists
        """
        if not force_reload and _scout_cache.count() > 0:
            return _scout_cache.get_all()

        query = "SELECT system_name, priority, added_by, added_at FROM scout_systems ORDER BY added_at"
        systems = await self.get_systems(query)
        _scout_cache.load(systems)  # Cache the results
        return systems

    async def reload_cache(self) -> None:
        """Reload the cache from the database"""
        query = "SELECT system_name, priority, added_by, added_at FROM scout_systems ORDER BY added_at"
        systems = await self.get_systems(query)
        _scout_cache.load(systems)
        log(f"Reloaded {len(systems)} scout systems into cache")

    async def bulk_add_systems(
        self, systems_data: list[tuple[str, str, str]]
    ) -> tuple[int, int]:
        """
        Bulk add systems to tracking
        Args:
            systems_data: List of (system_name, priority, added_by) tuples
        Returns:
            Tuple of (successful_adds, failed_adds)
        """
        successful = 0
        failed = 0

        for system_name, priority, added_by in systems_data:
            try:
                success = await self.add_system(system_name, priority, added_by)
                if success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                log(f"Error adding system {system_name}: {e}")
                failed += 1

        return successful, failed

    async def bulk_remove_systems(self, system_names: list[str]) -> tuple[int, int]:
        """
        Bulk remove systems from tracking
        Args:
            system_names: List of system names to remove
        Returns:
            Tuple of (successful_removes, failed_removes)
        """
        successful = 0
        failed = 0

        for system_name in system_names:
            try:
                success = await self.remove_system(system_name)
                if success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                log(f"Error removing system {system_name}: {e}")
                failed += 1

        return successful, failed

    async def remove_all_by_priority(self, priority: str) -> int:
        """
        Remove all systems of a specific priority
        Args:
            priority: Priority level to remove (Primary, Secondary, Tertiary)
        Returns:
            Number of systems removed
        """
        query = "DELETE FROM scout_systems WHERE priority = ?"
        await self.begin()
        cursor = await self.db().execute(query, [priority])
        await self.commit()

        # Update cache
        _scout_cache.remove_by_priority(priority)

        return cursor.rowcount

    @staticmethod
    def remove_duplicates(systems_to_scout):
        sys_names, systems_to_write = [], []
        for sys in systems_to_scout:
            if sys.system not in sys_names:
                systems_to_write.append(sys)
                sys_names.append(sys.system)
        return systems_to_write
