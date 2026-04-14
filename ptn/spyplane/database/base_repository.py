from sqlite3 import OperationalError

from aiosqlite import Connection


class BaseRepository:
    def db(self) -> Connection:
        from ptn.spyplane.bot_registry import get_bot  # noqa: PLC0415

        bot = get_bot()
        return bot.db

    @staticmethod
    async def begin():
        from ptn.spyplane.bot_registry import get_bot  # noqa: PLC0415

        bot = get_bot()
        try:
            await bot.db.execute("BEGIN")
        except OperationalError as e:
            if str(e) == "cannot start a transaction within a transaction":
                await bot.db.execute("END TRANSACTION")
                await bot.db.execute("BEGIN")

    @staticmethod
    async def rollback():
        from ptn.spyplane.bot_registry import get_bot  # noqa: PLC0415

        bot = get_bot()
        await bot.db.execute("ROLLBACK")

    @staticmethod
    async def commit():
        from ptn.spyplane.bot_registry import get_bot  # noqa: PLC0415

        bot = get_bot()
        await bot.db.execute("COMMIT")
