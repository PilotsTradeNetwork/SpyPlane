import discord
from discord.ext import tasks

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.database.config_repository import ConfigRepository
from ptn.spyplane.database.systems_repository import SystemsRepository

_PRIORITIES = ("Primary", "Secondary", "Tertiary")

# Embed titles used for pin-recovery matching
_SCOUT_EMBED_TITLE = "📡 Scouting Progress (This Tick)"
_REPORT_EMBED_TITLE = "📊 Scouting Totals (Since Last Change)"


class ScoutingProgressService:
    def __init__(self, repo=None, config_repo=None):
        self.repo = repo or SystemsRepository()
        self.config_repo = config_repo or ConfigRepository()
        # Instance-level message refs so the singleton always carries them
        self._scout_embed_message: discord.Message | None = None
        self._report_embed_message: discord.Message | None = None

    def start(self):
        self.update_progress_embeds.start()

    # ------------------------------------------------------------------
    # Background task
    # ------------------------------------------------------------------

    @tasks.loop(minutes=10)
    async def update_progress_embeds(self):
        log("[ScoutingProgressService] Running update_progress_embeds task")
        try:
            await self._refresh_scout_embed()
            await self._refresh_report_embed()
        except Exception as e:
            log_exception("update_progress_embeds", e)

    # ------------------------------------------------------------------
    # Embed refresh helpers
    # ------------------------------------------------------------------

    async def _refresh_scout_embed(self):
        bot = get_bot()
        if bot.channel is None:
            log("[ScoutingProgressService] bot.channel is None, skipping scout embed")
            return

        # Determine the cutoff timestamp: earliest added_at among posted systems
        posted_systems = await self.repo.get_posted_systems()
        if not posted_systems:
            cutoff = 0
        else:
            non_zero = [s.added_at for s in posted_systems if s.added_at != 0]
            cutoff = min(non_zero) if non_zero else 0

        scouted_counts = await self._count_scouted_since(cutoff)

        posted_totals: dict[str, int] = dict.fromkeys(_PRIORITIES, 0)
        for s in posted_systems:
            if s.priority in posted_totals:
                posted_totals[s.priority] += 1

        embed = self._build_tick_embed(scouted_counts, posted_totals)
        self._scout_embed_message = await self._post_or_edit(
            bot.channel, self._scout_embed_message, embed, _SCOUT_EMBED_TITLE
        )

    async def _refresh_report_embed(self):
        bot = get_bot()
        if bot.report_channel is None:
            log("[ScoutingProgressService] bot.report_channel is None, skipping report embed")
            return

        tracked_changed_at = int((await self.config_repo.get_config("tracked_changed_at")).value)

        scouted_counts = await self._count_scouted_since(tracked_changed_at)

        tracked_systems = await self.repo.get_all_tracked_systems()
        tracked_totals: dict[str, int] = dict.fromkeys(_PRIORITIES, 0)
        for s in tracked_systems:
            if s.priority in tracked_totals:
                tracked_totals[s.priority] += 1

        embed = self._build_total_embed(scouted_counts, tracked_totals)
        self._report_embed_message = await self._post_or_edit(
            bot.report_channel,
            self._report_embed_message,
            embed,
            _REPORT_EMBED_TITLE,
        )

    # ------------------------------------------------------------------
    # Embed builders
    # ------------------------------------------------------------------

    def _build_tick_embed(self, scouted_counts: dict[str, int], posted_totals: dict[str, int]) -> discord.Embed:
        embed = discord.Embed(
            title=_SCOUT_EMBED_TITLE,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="P.T.N. Spy Plane ™")

        any_field = False
        for priority in _PRIORITIES:
            total = posted_totals.get(priority, 0)
            if total == 0:
                continue
            scouted = scouted_counts.get(priority, 0)
            pct = int(scouted / total * 100) if total else 0
            embed.add_field(name=priority, value=f"{scouted}/{total} ({pct}%)", inline=False)
            any_field = True

        if not any_field:
            embed.description = "*No systems currently posted.*"

        embed.color = self._embed_color(scouted_counts, posted_totals)
        return embed

    def _build_total_embed(
        self,
        scouted_counts: dict[str, int],
        tracked_totals: dict[str, int],
    ) -> discord.Embed:
        embed = discord.Embed(title=_REPORT_EMBED_TITLE, timestamp=discord.utils.utcnow())
        embed.set_footer(text="P.T.N. Spy Plane ™")

        any_field = False
        for priority in _PRIORITIES:
            total = tracked_totals.get(priority, 0)
            if total == 0:
                continue
            scouted = scouted_counts.get(priority, 0)
            pct = int(scouted / total * 100) if total else 0
            embed.add_field(name=priority, value=f"{scouted}/{total} ({pct}%)", inline=False)
            any_field = True

        if not any_field:
            embed.description = "*No systems currently tracked.*"

        embed.color = self._embed_color(scouted_counts, tracked_totals)
        return embed

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def _count_scouted_since(self, since_ts: int) -> dict[str, int]:
        """Return a dict of priority -> count of unique systems scouted since *since_ts*."""
        query = (
            "SELECT DISTINCT sh.system_name, ss.priority "
            "FROM scout_history sh "
            "JOIN scout_systems ss ON sh.system_name = ss.system_name "
            "WHERE sh.timestamp >= ?"
        )
        bot = get_bot()
        async with bot.db.execute(query, [since_ts]) as cur:
            rows = await cur.fetchall()

        counts: dict[str, int] = dict.fromkeys(_PRIORITIES, 0)
        for _system_name, priority in rows:
            if priority in counts:
                counts[priority] += 1
        return counts

    @staticmethod
    def _embed_color(scouted: dict[str, int], totals: dict[str, int]) -> discord.Color:
        """Green if all tracked priorities are 100%, yellow if any >= 50%, red otherwise."""
        ratios = []
        for priority in _PRIORITIES:
            total = totals.get(priority, 0)
            if total == 0:
                continue
            ratios.append(scouted.get(priority, 0) / total)

        if not ratios:
            return discord.Color.greyple()
        if all(r >= 1.0 for r in ratios):
            return discord.Color.green()
        if any(r >= 0.5 for r in ratios):
            return discord.Color.yellow()
        return discord.Color.red()

    @staticmethod
    async def _find_in_pins(channel: discord.abc.Messageable, title: str) -> discord.Message | None:
        """Search the channel's pinned messages for a bot-authored embed matching *title*."""
        try:
            bot = get_bot()
            pins: list[discord.abc.PinnedMessage] = await channel.pins()
            for msg in pins:
                if msg.author.id != bot.user.id:
                    continue
                if msg.embeds and msg.embeds[0].title == title:
                    log(f"[ScoutingProgressService] Recovered message {msg.id} from pins (title: {title!r})")
                    return msg
        except Exception as e:
            log_exception("_find_in_pins", e)
        return None

    async def _post_or_edit(
        self,
        channel: discord.abc.Messageable,
        existing: discord.Message | None,
        embed: discord.Embed,
        title: str,
    ) -> discord.Message | None:
        """
        Edit *existing* if we have a valid ref.  When the ref is missing, try to
        recover it from pinned messages. If nothing is found, post a fresh message.
        """
        # --- attempt edit on known ref ---
        if not existing:
            existing = await ScoutingProgressService._find_in_pins(channel, title)
        if not existing:
            log(f"[ScoutingProgressService] Posting new embed message ({title!r})")
            return await channel.send(embed=embed)
        try:
            log(f"[ScoutingProgressService] Editing existing message {existing.id} ({title!r})")
            return await existing.edit(embed=embed)
        except discord.NotFound:
            log(f"[ScoutingProgressService] Message {existing.id} not found, will recover or repost ({title!r})")
        except discord.Forbidden:
            log(f"[ScoutingProgressService] No permission to edit message {existing.id} ({title!r})")
        except discord.HTTPException as e:
            log(f"[ScoutingProgressService] HTTP error editing message {existing.id} ({title!r}): {e}")


# Module-level singleton
_scouting_progress_service: ScoutingProgressService | None = None


def get_scouting_progress_service() -> ScoutingProgressService:
    global _scouting_progress_service  # noqa: PLW0603
    if _scouting_progress_service is None:
        _scouting_progress_service = ScoutingProgressService()
    return _scouting_progress_service
