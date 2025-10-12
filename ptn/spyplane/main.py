import asyncio

from discord.ext.prometheus import PrometheusCog

from ptn.spyplane.commands import Commands
from ptn.spyplane.constants import TOKEN
from ptn.spyplane.listeners import Listeners
from ptn.spyplane.spy_plane import bot


def run():
    Listeners()
    Commands()
    asyncio.run(spyplane())


async def spyplane():
    await bot.add_cog(PrometheusCog(bot))
    await bot.start(TOKEN)


if __name__ == "__main__":
    run()
