from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository

upsert_faction_state = """
INSERT INTO faction_states (system, faction, active_csv, pending_csv)
VALUES (?, ?, ?, ?)
ON CONFLICT (system, faction) 
DO UPDATE SET 
    active_csv = excluded.active_csv,
    pending_csv = excluded.pending_csv
"""

select_faction_state = """
SELECT system, faction, active_csv, pending_csv
FROM faction_states
WHERE system = ? AND faction = ?
"""

select_all_faction_states_for_system = """
SELECT system, faction, active_csv, pending_csv
FROM faction_states
WHERE system = ?
"""

delete_faction_state = """
DELETE FROM faction_states
WHERE system = ? AND faction = ?
"""


class FactionStatesRepository(BaseRepository):
    async def upsert_faction_state(
        self, system: str, faction: str, active_csv: str, pending_csv: str
    ) -> None:
        """
        Insert or update a faction state record.
        
        Args:
            system: System name
            faction: Faction name
            active_csv: Comma-separated active states
            pending_csv: Comma-separated pending states
        """
        await self.db().execute(
            upsert_faction_state, [system, faction, active_csv, pending_csv]
        )
        await self.db().commit()
        log(f"Upserted faction state: {system} - {faction}")

    async def get_faction_state(
        self, system: str, faction: str
    ) -> tuple[str, str, str, str] | None:
        """
        Get a faction state record.
        
        Args:
            system: System name
            faction: Faction name
            
        Returns:
            Tuple of (system, faction, active_csv, pending_csv) or None if not found
        """
        async with self.db().execute(select_faction_state, [system, faction]) as cur:
            row = await cur.fetchone()
            if row:
                return (row[0], row[1], row[2], row[3])
            return None

    async def get_all_faction_states_for_system(
        self, system: str
    ) -> list[tuple[str, str, str, str]]:
        """
        Get all faction states for a given system.
        
        Args:
            system: System name
            
        Returns:
            List of tuples (system, faction, active_csv, pending_csv)
        """
        async with self.db().execute(
            select_all_faction_states_for_system, [system]
        ) as cur:
            rows = await cur.fetchall()
            return [(row[0], row[1], row[2], row[3]) for row in rows]

    async def delete_faction_state(self, system: str, faction: str) -> None:
        """
        Delete a faction state record.
        
        Args:
            system: System name
            faction: Faction name
        """
        await self.db().execute(delete_faction_state, [system, faction])
        await self.db().commit()
        log(f"Deleted faction state: {system} - {faction}")

