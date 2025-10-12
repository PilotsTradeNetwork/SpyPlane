import datetime

import discord.message

from ptn.spyplane.constants import FACTION_SCOUT_ROLE_ID, log
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.models.scout_system import ScoutSystem
from ptn.spyplane.spy_plane import bot


class SystemsPostingService:
    def __init__(self, repo=SystemsRepository(), config_repo=ConfigRepository()):
        self.repo = repo
        self.config_repo = config_repo
        self.start_date = datetime.date(
            2022, 6, 18
        )  # start day randomly chosen for the daily sequence

    async def publish_systems_to_scout(self):
        tracked_systems = await self.repo.get_all_tracked_systems()
        should_carryover = (
            await self.config_repo.get_config("carryover")
        ).value.lower() in ["true", "yes", "y", "t"]
        carryover = []
        if should_carryover:
            carryover = await self.repo.get_carryover_systems()

        # Purge channel
        await self._purge_channel()

        splits = self.split_systems_by_priority(tracked_systems, carryover)

        # Log counts before posting
        log(
            f"Posting systems - Primary: {len(splits['Primary'])}, Secondary: {len(splits['Secondary'])}, Tertiary: {len(splits['Tertiary'])}"
        )

        await self.post_list(splits, "Primary")
        await self.post_list(splits, "Secondary")
        await self.post_list(splits, "Tertiary")

        if len(tracked_systems):
            await bot.channel.send(f"<@&{FACTION_SCOUT_ROLE_ID}> List Updated")

    async def post_list(self, splits, priority_string):
        systems_for_priority = splits[priority_string]

        if len(systems_for_priority):
            # Apply daily rotation logic based on priority
            daily_sequence = self._get_daily_sequence()

            if priority_string == "Primary":
                # Primary: Post all systems (no rotation)
                systems_to_post = systems_for_priority
            elif priority_string == "Secondary":
                # Secondary: Split into 2 groups, rotate every other day
                every_other_day = list(self.split(systems_for_priority, 2))
                systems_to_post = (
                    every_other_day[daily_sequence % 2] if every_other_day else []
                )
            elif priority_string == "Tertiary":
                # Tertiary: Split into 3 groups, rotate every third day
                every_third_day = list(self.split(systems_for_priority, 3))
                systems_to_post = (
                    every_third_day[daily_sequence % 3] if every_third_day else []
                )
            else:
                systems_to_post = systems_for_priority

            # Log the actual count that will be posted after rotation
            log(
                f"Posting {len(systems_to_post)} {priority_string} systems (day {daily_sequence})"
            )

            # Send header for non-Primary priorities
            if priority_string != "Primary":
                await bot.channel.send(f"__**{priority_string} List**__")

            # Write to database (only the systems we're actually posting)
            await self.repo.write_system_to_post(systems_to_post)

            # Post each system
            for scout_system in systems_to_post:
                message = await bot.channel.send(scout_system.system)
                await message.add_reaction(bot.emoji_bullseye)
        else:
            log(f"Empty {priority_string} List")

    async def _purge_channel(self):
        """Purge the channel of all non-pinned messages"""
        try:
            if bot.channel is None:
                log("[ERROR] bot.channel is None - cannot purge")
                return

            await bot.channel.purge(limit=None, check=self.is_not_pinned_message)
        except Exception as e:
            log(f"[ERROR] channel.purge failed: {e}")

            # Try alternative approach - delete messages individually
            try:
                messages = []
                async for message in bot.channel.history(limit=None):
                    if not message.pinned:
                        messages.append(message)

                for message in messages:
                    try:
                        await message.delete()
                    except Exception:
                        continue
            except Exception:
                pass

    @staticmethod
    def is_not_pinned_message(message: discord.message.Message) -> bool:
        return not message.pinned

    def split_systems_by_priority(
        self, systems: list[ScoutSystem], carryover: list[ScoutSystem]
    ) -> dict[str, list[ScoutSystem]]:
        """Split systems by priority without rotation (rotation happens in post_list)"""
        splits = {
            "Primary": [s for s in systems if s.priority == "Primary"],
            "Secondary": [s for s in systems if s.priority == "Secondary"],
            "Tertiary": [s for s in systems if s.priority == "Tertiary"],
        }

        # Add carryover systems
        return {
            "Primary": splits["Primary"],
            "Secondary": splits["Secondary"]
            + [
                s
                for s in carryover
                if s.priority == "Secondary"
                and s.system not in [l.system for l in splits["Secondary"]]
            ],
            "Tertiary": splits["Tertiary"]
            + [
                s
                for s in carryover
                if s.priority == "Tertiary"
                and s.system not in [l.system for l in splits["Tertiary"]]
            ],
        }

    def _get_daily_sequence(self) -> int:
        """Calculate daily sequence based on start date"""
        today = datetime.date.today()
        days_since_start = (today - self.start_date).days
        return days_since_start

    @staticmethod  # https://stackoverflow.com/questions/2130016/splitting-a-list-into-n-parts-of-approximately-equal-length
    def split(array, split_size):
        k, m = divmod(len(array), split_size)
        return (
            array[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)]
            for i in range(split_size)
        )
