from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ScoutSystem:
    """Holds one tracked system from the database"""

    system: str
    priority: str
    added_by: str = ""
    added_at: int = 0

    def __post_init__(self):
        if self.added_at == 0:
            self.added_at = int(datetime.now(UTC).timestamp())
