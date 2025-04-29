from dataclasses import dataclass
import math
from typing import Union

TICKS_PER_SECOND = 20

@dataclass(frozen=True)
class GameTime:
    """Represents a duration in game time, stored internally as ticks."""
    _ticks: int

    def __post_init__(self):
        if self._ticks < 0:
            raise ValueError("GameTime cannot be negative")

    @classmethod
    def from_ticks(cls, ticks: int) -> 'GameTime':
        """Creates a GameTime object from a duration in game ticks."""
        return cls(ticks)

    @classmethod
    def from_seconds(cls, seconds: Union[int, float]) -> 'GameTime':
        """Creates a GameTime object from a duration in seconds."""
        if seconds < 0:
            raise ValueError("Duration in seconds cannot be negative")
        ticks = math.ceil(seconds * TICKS_PER_SECOND)
        return cls(ticks)

    def as_ticks(self) -> int:
        """Returns the duration in game ticks."""
        return self._ticks

    def as_seconds(self) -> float:
        """Returns the duration in seconds."""
        return self._ticks / TICKS_PER_SECOND

    def __str__(self) -> str:
        return f"{self.as_seconds():.2f}s ({self._ticks} ticks)"

    def __repr__(self) -> str:
        return f"GameTime(ticks={self._ticks})"
