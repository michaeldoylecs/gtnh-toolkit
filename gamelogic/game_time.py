from dataclasses import dataclass
import math
from typing import Union

TICKS_PER_SECOND = 20

@dataclass(frozen=True)
class GameTime:
    """Represents a duration in game time, stored internally as seconds for precision."""
    _internal_seconds: float

    def __post_init__(self):
        if self._internal_seconds < 0:
            raise ValueError("GameTime duration cannot be negative")

    @classmethod
    def from_ticks(cls, ticks: int) -> 'GameTime':
        """Creates a GameTime object from a duration in game ticks."""
        if not isinstance(ticks, int):
            raise TypeError("Ticks must be an integer")
        if ticks < 0:
            raise ValueError("Ticks cannot be negative")
        calculated_seconds = float(ticks) / TICKS_PER_SECOND
        return cls(_internal_seconds=calculated_seconds)

    @classmethod
    def from_seconds(cls, seconds: Union[int, float]) -> 'GameTime':
        """Creates a GameTime object from a duration in seconds."""
        if seconds < 0:
            raise ValueError("Duration in seconds cannot be negative")
        return cls(_internal_seconds=float(seconds))

    def as_ticks(self) -> int:
        """Returns the duration in game ticks as a float for precision."""
        return int(math.ceil(self._internal_seconds * TICKS_PER_SECOND))

    def as_seconds(self) -> float:
        """Returns the duration in seconds, rounded to the nearest tick."""
        return roundToBase(self._internal_seconds / TICKS_PER_SECOND, 0.05)

    def as_exact_seconds(self) -> float:
        """Returns the duration in seconds."""
        return self._internal_seconds

    def __str__(self) -> str:
        # Display seconds with a reasonable precision, and ticks potentially as float
        ticks_display = self.as_ticks()
        if ticks_display == int(ticks_display):
            ticks_str = f"{int(ticks_display)} ticks"
        else:
            ticks_str = f"{ticks_display:.2f} ticks" # Or more precision if desired
        return f"{self.as_seconds():.3f}s ({ticks_str})"

    def __repr__(self) -> str:
        return f"GameTime(seconds={self._internal_seconds})"

    # Basic arithmetic operations
    def __add__(self, other: 'GameTime') -> 'GameTime':
        if not isinstance(other, GameTime):
            return NotImplemented
        return GameTime.from_seconds(self.as_seconds() + other.as_seconds())

    def __sub__(self, other: 'GameTime') -> 'GameTime':
        if not isinstance(other, GameTime):
            return NotImplemented
        new_seconds = self.as_seconds() - other.as_seconds()
        # __post_init__ will handle if new_seconds is negative.
        return GameTime.from_seconds(new_seconds)

    def __mul__(self, scalar: Union[int, float]) -> 'GameTime':
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar < 0:
            raise ValueError("Cannot multiply GameTime by a negative scalar")
        return GameTime.from_seconds(self.as_seconds() * scalar)

    def __rmul__(self, scalar: Union[int, float]) -> 'GameTime':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Union[int, float]) -> 'GameTime':
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar <= 0: # Cannot divide by zero or a negative number to get a valid duration
            raise ValueError("Cannot divide GameTime by zero or a negative scalar")
        return GameTime.from_seconds(self.as_seconds() / scalar)

    # Comparison operators
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameTime):
            return NotImplemented
        # Compare based on a small tolerance for floating point numbers
        return abs(self._internal_seconds - other._internal_seconds) < 1e-9

    def __lt__(self, other: 'GameTime') -> bool:
        if not isinstance(other, GameTime):
            return NotImplemented
        return self._internal_seconds < other._internal_seconds

    def __le__(self, other: 'GameTime') -> bool:
        if not isinstance(other, GameTime):
            return NotImplemented
        return self._internal_seconds <= other._internal_seconds or self.__eq__(other)

    def __gt__(self, other: 'GameTime') -> bool:
        if not isinstance(other, GameTime):
            return NotImplemented
        return self._internal_seconds > other._internal_seconds

    def __ge__(self, other: 'GameTime') -> bool:
        if not isinstance(other, GameTime):
            return NotImplemented
        return self._internal_seconds >= other._internal_seconds or self.__eq__(other)

def roundToBase(x: Union[int, float], base: Union[int, float])-> float:
    return float(base * round(x / base))
