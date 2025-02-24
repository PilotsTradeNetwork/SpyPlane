import asyncio

from discord.ext.prometheus import PrometheusCog

from spyplane.commands import Commands
from spyplane.constants import TOKEN
from spyplane.listeners import Listeners
from spyplane.spy_plane import bot


def run():
    Listeners()
    Commands()
    asyncio.run(spyplane())


async def spyplane():
    await bot.add_cog(PrometheusCog(bot))
    await bot.start(TOKEN)


if __name__=='__main__':
    run()
