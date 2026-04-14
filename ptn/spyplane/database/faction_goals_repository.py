import time
from datetime import datetime, timezone

from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository
from ptn.spyplane.database.config_repository import ConfigRepository

# Note: "index" is a reserved keyword in SQLite, so it must be quoted in all SQL queries
insert_goal = """
INSERT INTO faction_goals ("index", system, faction_one, faction_other, goalkind, additional_note)
VALUES (?, ?, ?, ?, ?, ?)
"""

delete_goal = """
DELETE FROM faction_goals
WHERE "index" = ?
"""

delete_all_goals = """
DELETE FROM faction_goals
"""

select_all_goals = """
SELECT "index", system, faction_one, faction_other, goalkind, additional_note
FROM faction_goals
ORDER BY "index"
"""

select_goal_by_index = """
SELECT "index", system, faction_one, faction_other, goalkind, additional_note
FROM faction_goals
WHERE "index" = ?
"""

update_goal = """
UPDATE faction_goals
SET system = ?, faction_one = ?, faction_other = ?, goalkind = ?, additional_note = ?
WHERE "index" = ?
"""


class FactionGoalsRepository(BaseRepository):
    def __init__(self, config_repo=None):
        super().__init__()
        self.config_repo = config_repo or ConfigRepository()

    async def add_goal(
        self,
        index: int,
        system: str,
        faction_one: str,
        faction_other: str,
        goalkind: str,
        additional_note: str | None = None,
    ) -> None:
        try:
            await self.begin()
            await self.db().execute(insert_goal, [index, system, faction_one, faction_other, goalkind, additional_note])
            await self.commit()
            log(f"Added faction goal: index={index}, system={system}, goalkind={goalkind}")
        except Exception:
            await self.rollback()
            raise

    async def remove_goal(self, index: int) -> bool:
        try:
            await self.begin()
            cursor = await self.db().execute(delete_goal, [index])
            await self.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                log(f"Removed faction goal: index={index}")
            return deleted
        except Exception:
            await self.rollback()
            raise

    async def remove_all_goals(self) -> int:
        """Remove all goals and return the number of goals removed"""
        try:
            await self.begin()
            cursor = await self.db().execute(delete_all_goals)
            await self.commit()
            count = cursor.rowcount
            if count > 0:
                log(f"Removed all {count} faction goals")
            return count
        except Exception:
            await self.rollback()
            raise

    async def get_all_goals(
        self,
    ) -> list[tuple[int, str, str, str, str, str | None]]:
        async with self.db().execute(select_all_goals) as cur:
            rows = await cur.fetchall()
            return [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]

    async def update_goal(
        self,
        index: int,
        system: str,
        faction_one: str,
        faction_other: str,
        goalkind: str,
        additional_note: str | None = None,
    ) -> bool:
        try:
            await self.begin()
            cursor = await self.db().execute(
                update_goal, [system, faction_one, faction_other, goalkind, additional_note, index]
            )
            await self.commit()
            updated = cursor.rowcount > 0
            if updated:
                log(f"Updated faction goal: index={index}, system={system}, goalkind={goalkind}")
            return updated
        except Exception:
            await self.rollback()
            raise

    async def get_goal_by_index(self, index: int) -> tuple[int, str, str, str, str, str | None] | None:
        async with self.db().execute(select_goal_by_index, [index]) as cur:
            row = await cur.fetchone()
            if row:
                return (row[0], row[1], row[2], row[3], row[4], row[5])
            return None

    async def get_message_id(self) -> int | None:
        get_config_query = """
        SELECT value FROM configuration WHERE name = ?
        """
        try:
            async with self.db().execute(get_config_query, ["faction_goals_message_id"]) as cur:
                row = await cur.fetchone()
            if row and row[0]:
                return int(row[0])
            return None
        except (ValueError, TypeError):
            # Value is invalid (not a number)
            return None

    async def set_message_id(self, message_id: int | None) -> None:
        value = str(message_id) if message_id else ""
        timestamp = int(time.mktime(datetime.now(timezone.utc).timetuple()))

        # Check if config exists, then update or insert
        check_config = """
        SELECT id FROM configuration WHERE name = ?
        """

        insert_config = """
        INSERT INTO configuration (name, value, timestamp)
        VALUES (?, ?, ?)
        """

        update_config = """
        UPDATE configuration
        SET value=?, timestamp=?
        WHERE name=?
        """

        try:
            await self.begin()
            async with self.db().execute(check_config, ["faction_goals_message_id"]) as cur:
                row = await cur.fetchone()

            if row:
                # Config exists, update it
                await self.db().execute(
                    update_config,
                    [value, timestamp, "faction_goals_message_id"],
                )
            else:
                # Config doesn't exist, insert it
                await self.db().execute(
                    insert_config,
                    ["faction_goals_message_id", value, timestamp],
                )
            await self.commit()
        except Exception:
            await self.rollback()
            raise
