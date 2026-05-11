from __future__ import annotations

import math
from dataclasses import dataclass

import httpx

from ptn.spyplane.constants import log

EDSM_SYSTEMS_URL = "https://www.edsm.net/api-v1/systems"
FAR_AWAY_THRESHOLD = 500


@dataclass
class EdsmSystem:
    name: str
    distance: int  # rounded distance from origin in ly
    is_populated: bool  # True if .information is non-empty


async def fetch_edsm_systems(system_names: list[str]) -> dict[str, EdsmSystem | None]:
    """
    Bulk-fetch system data from EDSM for all given names in a single HTTP request.

    Returns a dict mapping each requested name (case-insensitive match) to an
    EdsmSystem, or None if the system was not found in EDSM.
    """
    if not system_names:
        return {}

    params: list[tuple[str, str | int]] = [
        ("showCoordinates", 1),
        ("showInformation", 1),
        *[("systemName[]", name) for name in system_names],
    ]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(EDSM_SYSTEMS_URL, params=params)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        log(f"EDSM bulk lookup failed: {e}")
        return dict.fromkeys(system_names)

    result: dict[str, EdsmSystem | None] = dict.fromkeys(system_names)

    for entry in data:
        entry_name = entry.get("name")
        if not entry_name:
            continue
        coords = entry.get("coords", {})
        x = coords.get("x", 0)
        y = coords.get("y", 0)
        z = coords.get("z", 0)
        distance = round(math.sqrt(x * x + y * y + z * z))
        is_populated = bool(entry.get("information"))
        system = EdsmSystem(name=entry_name, distance=distance, is_populated=is_populated)
        # Match back to requested names case-insensitively
        for requested in system_names:
            if requested.lower() == entry_name.lower():
                result[requested] = system
                break

    return result
