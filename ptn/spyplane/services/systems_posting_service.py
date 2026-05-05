from datetime import UTC, datetime, timedelta

import discord.message

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import FACTION_SCOUT_ROLE_ID, log
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.database.scout_history_repository import ScoutHistoryRepository
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.models.scout_system import ScoutSystem


class SystemsPostingService:
    def __init__(self, repo=None, config_repo=None, history_repo=None):
        self.repo = repo or SystemsRepository()
        self.config_repo = config_repo or ConfigRepository()
        self.history_repo = history_repo or ScoutHistoryRepository()

    async def publish_systems_to_scout(self):
        bot = get_bot()
        tracked_systems = await self.repo.get_all_tracked_systems()

        # Purge channel and posted systems table so totals reflect only what is currently posted
        await self.repo.purge_posted_systems()
        await self._purge_channel()

        splits = await self.split_systems_by_priority(tracked_systems)

        # Log counts before posting
        log(
            f"Posting systems - Primary: {len(splits['Primary'])}, Secondary: {len(splits['Secondary'])}, Tertiary: {len(splits['Tertiary'])}"
        )

        await self.post_list(splits, "Primary")
        await self.post_list(splits, "Secondary")
        await self.post_list(splits, "Tertiary")

        if len(tracked_systems):
            await bot.channel.send(f"<@&{FACTION_SCOUT_ROLE_ID}> List Updated\nLink to top: {first_message.jump_url}")

    async def post_list(self, splits, priority_string):
        bot = get_bot()
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
            return None

        first_message = None
        log(f"Posting {len(systems_for_priority)} {priority_string} systems")

        # Send header for non-Primary priorities
        if priority_string != "Primary":
            await bot.channel.send(f"__**{priority_string} List**__")

        # Post each system and collect message IDs
        message_ids = {}
        for scout_system in systems_for_priority:
            message = await bot.channel.send(scout_system.system)
            await message.add_reaction(bot.emoji_bullseye)
            message_ids[scout_system.system] = message.id
            if not first_message:
                first_message = message

        # Write to database with message IDs
        await self.repo.write_system_to_post(systems_for_priority, message_ids)

        return first_message

    async def _purge_channel(self):
        bot = get_bot()
        try:
            if bot.channel is None:
                log("[ERROR] bot.channel is None - cannot purge")
                return

            await bot.channel.purge(limit=None, check=self.is_not_pinned_message)
        except Exception as e:
            log(f"[ERROR] channel.purge failed: {e}")

            # Try alternative approach - delete messages individually
            try:
                messages = [message async for message in bot.channel.history(limit=None) if not message.pinned]
                for message in messages:
                    await message.delete()
            except Exception as e:
                log(f"[ERROR] fallback message deletion failed: {e}")

    @staticmethod
    def is_not_pinned_message(message: discord.message.Message) -> bool:
        return not message.pinned

    async def split_systems_by_priority(
        self,
        systems: list[ScoutSystem],
    ) -> dict[str, list[ScoutSystem]]:
        # Read per-priority limits and selection mode from config
        primary_limit = int((await self.config_repo.get_config("primary_limit")).value)
        secondary_limit = int((await self.config_repo.get_config("secondary_limit")).value)
        tertiary_limit = int((await self.config_repo.get_config("tertiary_limit")).value)
        selection_mode = (await self.config_repo.get_config("selection_mode")).value.lower()

        # Determine recently-scouted systems to hide from the list
        now = datetime.now(UTC)
        scouted_1d = await self.history_repo.get_systems_scouted_since((now - timedelta(days=1)).timestamp())
        scouted_2d = await self.history_repo.get_systems_scouted_since((now - timedelta(days=2)).timestamp())

        splits = {
            "Primary": [s for s in systems if s.priority == "Primary"],
            "Secondary": [s for s in systems if s.priority == "Secondary" and s.system not in scouted_1d],
            "Tertiary": [s for s in systems if s.priority == "Tertiary" and s.system not in scouted_2d],
        }

        # Apply selection_mode sorting before limiting
        if selection_mode == "oldest_first":
            # Sort ascending by added_at; treat 0 as very large (sort last)
            def sort_key(s: ScoutSystem) -> int:
                return s.added_at if s.added_at != 0 else 2**62

            for priority, bucket in splits.items():
                splits[priority] = sorted(bucket, key=sort_key)
        # For 'absolute', keep the insertion order returned by get_all_tracked_systems

        # Apply per-priority limits (0 = no limit)
        if primary_limit > 0:
            splits["Primary"] = splits["Primary"][:primary_limit]
        if secondary_limit > 0:
            splits["Secondary"] = splits["Secondary"][:secondary_limit]
        if tertiary_limit > 0:
            splits["Tertiary"] = splits["Tertiary"][:tertiary_limit]

        return splits
