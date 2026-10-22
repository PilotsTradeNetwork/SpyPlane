from __future__ import annotations

import math
from dataclasses import dataclass

import httpx

from ptn.spyplane.constants import log

EDSM_SYSTEMS_URL = "https://www.edsm.net/api-v1/systems"
FAR_AWAY_THRESHOLD = 500
EDSM_CHUNK_SIZE = 50  # names per request, keeps the URL length sane


@dataclass
class EdsmSystem:
    name: str
    distance: int  # rounded distance from origin in ly
    is_populated: bool  # True if .information is non-empty
    coords: tuple[float, float, float] | None = None  # None if EDSM has no coordinates


async def fetch_edsm_systems(system_names: list[str]) -> dict[str, EdsmSystem | None]:
    """
    Bulk-fetch system data from EDSM, in chunks of EDSM_CHUNK_SIZE names per request.

    Returns a dict mapping each requested name (case-insensitive match) to an
    EdsmSystem, or None if the system was not found in EDSM or its request failed.
    """
    result: dict[str, EdsmSystem | None] = dict.fromkeys(system_names)
    if not system_names:
        return result

    requested_by_lower = {name.lower(): name for name in system_names}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for start in range(0, len(system_names), EDSM_CHUNK_SIZE):
            params: list[tuple[str, str | int]] = [
                ("showCoordinates", 1),
                ("showInformation", 1),
                *[("systemName[]", name) for name in system_names[start : start + EDSM_CHUNK_SIZE]],
            ]
            try:
                response = await client.get(EDSM_SYSTEMS_URL, params=params)  # type: ignore[arg-type]
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                log(f"EDSM bulk lookup failed: {e}")
                continue

            # EDSM returns {} instead of [] when nothing matches
            for entry in data if isinstance(data, list) else []:
                entry_name = entry.get("name")
                requested = requested_by_lower.get(entry_name.lower()) if entry_name else None
                if requested is None:
                    continue
                raw = entry.get("coords")
                coords = (raw["x"], raw["y"], raw["z"]) if raw else None
                distance = round(math.dist(coords, (0, 0, 0))) if coords else 0
                result[requested] = EdsmSystem(
                    name=entry_name,
                    distance=distance,
                    is_populated=bool(entry.get("information")),
                    coords=coords,
                )

    return result
