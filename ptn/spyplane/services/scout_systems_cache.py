from typing import Optional

from ptn.spyplane.models.scout_system import ScoutSystem


class ScoutSystemsCache:
    """In-memory cache for scout systems"""

    _instance: Optional["ScoutSystemsCache"] = None
    _systems: dict[str, ScoutSystem] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, systems: list[ScoutSystem]) -> None:
        """Load systems into cache"""
        self._systems = {system.system: system for system in systems}

    def get_all(self) -> list[ScoutSystem]:
        """Get all cached systems"""
        return list(self._systems.values())

    def get(self, system_name: str) -> ScoutSystem | None:
        """Get a system by name"""
        return self._systems.get(system_name)

    def add(self, system: ScoutSystem) -> None:
        """Add a system to cache"""
        self._systems[system.system] = system

    def remove(self, system_name: str) -> bool:
        """Remove a system from cache. Returns True if removed, False if not found."""
        if system_name in self._systems:
            del self._systems[system_name]
            return True
        return False

    def remove_by_priority(self, priority: str) -> int:
        """Remove all systems of a specific priority. Returns count removed."""
        to_remove = [name for name, system in self._systems.items() if system.priority == priority]
        for name in to_remove:
            del self._systems[name]
        return len(to_remove)

    def clear(self) -> None:
        """Clear the cache"""
        self._systems.clear()

    def count(self) -> int:
        """Get count of cached systems"""
        return len(self._systems)
