from enum import Enum
import math

class VoltageTier(Enum):
    # Tiers now start from 1
    LV = 1
    MV = 2
    HV = 3
    EV = 4
    IV = 5
    LUV = 6
    ZPM = 7
    UV = 8
    UHV = 9
    UEV = 10
    UIV = 11
    UMV = 12
    UXV = 13
    MAX = 14

    @property
    def max_voltage(self):
        return Voltage.from_tier(self)
    
    # min_voltage property might need adjustment or removal if ULV is gone
    # For now, let's assume LV's min voltage is 0 conceptually
    @property
    def min_voltage(self):
        if self == VoltageTier.LV:
             # Or perhaps return Voltage(0)? Depends on desired behavior.
             # Let's return the voltage corresponding to the start of the tier below,
             # which for LV (tier 1) doesn't exist in the same way.
             # Returning 0 seems reasonable.
            return Voltage(0)
        else:
            # Get the tier below the current one
            previous_tier = VoltageTier.from_tier_num(self.value - 1)
            # Return the max voltage of that previous tier + 1 (or just the start of the current tier?)
            # Let's return the voltage calculated by from_tier for the tier below.
            return Voltage.from_tier(previous_tier)

    @classmethod
    def from_tier_num(cls, tier_num: int) -> 'VoltageTier':
        # Clamp between 1 (LV) and 14 (MAX)
        tier_num = max(1, min(14, tier_num))
        # Enum values start at 1, but list index starts at 0
        return list(cls)[tier_num - 1]

    @classmethod
    def from_name(cls, name: str) -> 'VoltageTier':
        """Get a VoltageTier enum from its string name.
        
        Args:
            name: The name of the voltage tier (e.g., 'ULV', 'MV', 'HV')
        
        Returns:
            The corresponding VoltageTier enum value
            
        Raises:
            ValueError: If the name doesn't match any VoltageTier
        """
        try:
            return cls[name.upper()]
        except KeyError:
            raise ValueError(f"No VoltageTier with name '{name}'")

    def __str__(self) -> str:
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, VoltageTier):
            return self.value == other.value
        return False

    def __lt__(self, other):
        if isinstance(other, VoltageTier):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, VoltageTier):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, VoltageTier):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, VoltageTier):
            return self.value >= other.value
        return NotImplemented

class Voltage:
    def __init__(self, voltage: int):
        self.voltage = max(0, voltage)  # Ensure voltage is non-negative
    
    @property
    def tier(self) -> VoltageTier:
        # Special case for 0 voltage maps to LV (tier 1)
        if self.voltage == 0:
            return VoltageTier.LV

        # Calculate tier based on voltage
        # Base tier number (1 for LV range [0-31], 2 for MV range [32-127], etc.)
        # Clamp voltage >= 1 for log
        voltage_for_log = max(1, self.voltage)
        tier_num_float = math.log(voltage_for_log / 8, 4)
        tier_num = math.floor(tier_num_float)

        # Clamp result between 1 (LV) and 14 (MAX)
        tier_num = min(14, max(1, tier_num))
        return VoltageTier.from_tier_num(tier_num)

    @classmethod
    def from_tier(cls, tier: VoltageTier) -> 'Voltage':
        # Calculate MAX voltage for the tier
        # Use base voltage 32 and adjust exponent since LV is 1 (tier.value - 1)
        # V_max(T) = 32 * 4^(T-1)
        voltage = 32 * (4 ** (tier.value - 1))
        return cls(voltage)

    def __eq__(self, other):
        if isinstance(other, Voltage):
            return self.voltage == other.voltage
        return False
    
    def __repr__(self):
        return f"Voltage({self.voltage}, {self.tier})"

    def __add__(self, other):
        if isinstance(other, Voltage):
            return Voltage(self.voltage + other.voltage)
        elif isinstance(other, (int, float)):
            return Voltage(self.voltage + int(other))
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Voltage):
            return Voltage(self.voltage - other.voltage)
        elif isinstance(other, (int, float)):
            return Voltage(self.voltage - int(other))
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return Voltage(int(other) - self.voltage)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Voltage(int(self.voltage * other))
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Voltage):
            return self.voltage / other.voltage
        elif isinstance(other, (int, float)):
            return Voltage(int(self.voltage / other))
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return Voltage(int(other / self.voltage))
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Voltage):
            return self.voltage < other.voltage
        elif isinstance(other, (int, float)):
            return self.voltage < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Voltage):
            return self.voltage <= other.voltage
        elif isinstance(other, (int, float)):
            return self.voltage <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Voltage):
            return self.voltage > other.voltage
        elif isinstance(other, (int, float)):
            return self.voltage > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Voltage):
            return self.voltage >= other.voltage
        elif isinstance(other, (int, float)):
            return self.voltage >= other
        return NotImplemented

    def __int__(self):
        return self.voltage

    def __float__(self):
        return float(self.voltage)
