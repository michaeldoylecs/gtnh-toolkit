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
        # Base tier number (0 for LV range [0-31], 1 for MV range [32-127], etc.)
        # Use max(1, self.voltage) to avoid log(0) or negative logs
        # Use base voltage 32
        # Example: voltage=31 -> log(31/32, 4) approx -0.02 -> ceil is 0.
        # Example: voltage=32 -> log(32/32, 4) = log(1, 4) = 0 -> ceil is 0. Needs adjustment.
        # Let's rethink the formula slightly. We want tier N if V is in [32*4^(N-1), 32*4^N - 1]
        # For LV (N=1): [32*4^0, 32*4^1 - 1] = [32, 127] -> This isn't right, LV should include lower voltages.
        # Let's define tiers by their MAX voltage: LV max=31, MV max=127, HV max=511 etc.
        # Max voltage for tier T (starting T=1 for LV) is 32 * 4^(T-1) - 1 ? No, that's not right either.
        # Max voltage *for* tier T (value T) is V_max(T) = 8 * 4^T. (Using the old formula base)
        # Let's use the definition: Tier T contains voltages V such that V_max(T-1) < V <= V_max(T)
        # Where V_max(T) = 32 * 4^(T-1) for T >= 1 (LV=1, MV=2...)
        # V_max(LV=1) = 32 * 4^0 = 32
        # V_max(MV=2) = 32 * 4^1 = 128
        # V_max(HV=3) = 32 * 4^2 = 512
        # So, LV range is (0, 32], MV is (32, 128], HV is (128, 512]
        # We need to find T such that 32 * 4^(T-2) < self.voltage <= 32 * 4^(T-1)
        # Divide by 32: 4^(T-2) < self.voltage / 32 <= 4^(T-1)
        # Take log base 4: T-2 < log4(self.voltage / 32) <= T-1
        # Add 1: T-1 < log4(self.voltage / 32) + 1 <= T
        # So, T = ceil(log4(self.voltage / 32) + 1)
        # Let's test:
        # V=32: ceil(log4(1)+1) = ceil(0+1) = 1. Should be MV (T=2). Formula is off by 1.
        # Let's try T = floor(log4(self.voltage / 8)) ? No, base is 32.
        # Try T = floor(log4(self.voltage / 32)) + 2 ?
        # V=32: floor(log4(1)) + 2 = 0 + 2 = 2 (MV). Correct.
        # V=128: floor(log4(4)) + 2 = 1 + 2 = 3 (HV). Correct.
        # V=31: floor(log4(31/32)) + 2 = floor(-0.02) + 2 = -1 + 2 = 1 (LV). Correct.
        # V=8: floor(log4(8/32)) + 2 = floor(log4(0.25)) + 2 = floor(-1) + 2 = -1 + 2 = 1 (LV). Correct.
        # Need max(1, ...) because log of value < 8 would yield results mapping below LV.
        # Let's use voltage >= 1 for log calculation.
        if self.voltage < 8: # Voltages below 8 are LV
             return VoltageTier.LV
        # Use floor(log4(V/8)) + 1 ? Let's stick to the derived formula.
        # Clamp voltage >= 1 for log
        voltage_for_log = max(1, self.voltage)
        tier_num_float = math.log(voltage_for_log / 32, 4) + 2
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
