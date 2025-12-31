from ptn.spyplane.constants import log
from ptn.spyplane.database.base_repository import BaseRepository

select_header_footer = """
SELECT header, footer
FROM faction_header_footer
WHERE id = 1
"""

update_footer = """
UPDATE faction_header_footer
SET footer = ?
WHERE id = 1
"""

update_header = """
UPDATE faction_header_footer
SET header = ?
WHERE id = 1
"""

insert_header_footer = """
INSERT INTO faction_header_footer (id, header, footer)
VALUES (1, ?, ?)
ON CONFLICT(id) DO UPDATE SET header = excluded.header, footer = excluded.footer
"""


class FactionHeaderFooterRepository(BaseRepository):
    async def get_header_footer(self) -> tuple[str, str]:
        async with self.db().execute(select_header_footer) as cur:
            row = await cur.fetchone()
            if row:
                return (row[0] or "", row[1] or "")
            return ("", "")

    async def update_footer(self, footer: str) -> None:
        try:
            await self.begin()
            cursor = await self.db().execute(update_footer, [footer])
            if cursor.rowcount == 0:
                await self.db().execute(insert_header_footer, ["", footer])
            await self.commit()
            log(f"Updated faction goals footer")
        except Exception as e:
            await self.rollback()
            raise

    async def update_header(self, header: str) -> None:
        try:
            await self.begin()
            cursor = await self.db().execute(update_header, [header])
            if cursor.rowcount == 0:
                await self.db().execute(insert_header_footer, [header, ""])
            await self.commit()
            log(f"Updated faction goals header")
        except Exception as e:
            await self.rollback()
            raise

    async def update_header_footer(self, header: str | None, footer: str | None) -> None:
        try:
            await self.begin()
            # Get current values
            current_header, current_footer = await self.get_header_footer()
            
            # Use provided values or keep current ones
            new_header = header if header is not None else current_header
            new_footer = footer if footer is not None else current_footer
            
            await self.db().execute(insert_header_footer, [new_header, new_footer])
            await self.commit()
            log(f"Updated faction goals header and/or footer")
        except Exception as e:
            await self.rollback()
            raise

