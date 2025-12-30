from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository

insert_faction_state = """
INSERT INTO faction_states (system, faction, active_csv, pending_csv, influence, controlling)
VALUES (?, ?, ?, ?, ?, ?)
"""

delete_all_faction_states_for_system = """
DELETE FROM faction_states
WHERE system = ?
"""

select_faction_state = """
SELECT system, faction, active_csv, pending_csv, influence, controlling
FROM faction_states
WHERE system = ? AND faction = ?
"""

select_all_faction_states_for_system = """
SELECT system, faction, active_csv, pending_csv, influence, controlling
FROM faction_states
WHERE system = ?
"""

select_ptn_influence_warnings = """
SELECT system, faction, influence, controlling
FROM faction_states
WHERE faction = 'Pilots Trade Network'
  AND influence > 0.65
ORDER BY influence DESC
"""

delete_faction_state = """
DELETE FROM faction_states
WHERE system = ? AND faction = ?
"""


class FactionStatesRepository(BaseRepository):
    async def replace_faction_states_for_system(
        self, faction_states: list[dict]
    ) -> None:
        if not faction_states:
            return
        
        system = faction_states[0]["system"]
        
        try:
            await self.begin()
            await self.db().execute(delete_all_faction_states_for_system, [system])
            
            for state_data in faction_states:
                await self.db().execute(
                    insert_faction_state,
                    [
                        state_data["system"],
                        state_data["faction"],
                        state_data["active_csv"],
                        state_data["pending_csv"],
                        state_data.get("influence"),
                        state_data.get("controlling", 0),
                    ],
                )
            
            await self.commit()
            log(f"Replaced {len(faction_states)} faction states for system: {system}")
        except Exception as e:
            await self.rollback()
            raise

    async def get_faction_state(
        self, system: str, faction: str
    ) -> tuple[str, str, str, str, float | None, int] | None:
        async with self.db().execute(select_faction_state, [system, faction]) as cur:
            row = await cur.fetchone()
            if row:
                return (row[0], row[1], row[2], row[3], row[4], row[5])
            return None

    async def get_all_faction_states_for_system(
        self, system: str
    ) -> list[tuple[str, str, str, str, float | None, int]]:
        async with self.db().execute(
            select_all_faction_states_for_system, [system]
        ) as cur:
            rows = await cur.fetchall()
            return [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]

    async def get_ptn_influence_warnings(
        self
    ) -> list[tuple[str, str, float, int]]:
        async with self.db().execute(select_ptn_influence_warnings) as cur:
            rows = await cur.fetchall()
            return [(row[0], row[1], row[2], row[3]) for row in rows]

    async def delete_faction_state(self, system: str, faction: str) -> None:
        try:
            await self.begin()
            await self.db().execute(delete_faction_state, [system, faction])
            await self.commit()
            log(f"Deleted faction state: {system} - {faction}")
        except Exception as e:
            await self.rollback()
            raise

