from enum import Enum
import math

class VoltageTier(Enum):
    ULV = 0
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
    
    @property
    def min_voltage(self):
        if self == VoltageTier.ULV:
            return 0
        else:
            return Voltage.from_tier(VoltageTier.from_tier_num(self.value - 1))
    
    @classmethod
    def from_tier_num(cls, tier_num: int) -> 'VoltageTier':
        tier_num = max(0, min(14, tier_num))
        return list(cls)[tier_num]
    
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

class Voltage:
    def __init__(self, voltage: int):
        self.voltage = max(0, voltage)  # Ensure voltage is non-negative
    
    @property
    def tier(self) -> VoltageTier:
        # Special case for 0 voltage
        if self.voltage == 0:
            return VoltageTier.ULV
        
        # Calculate tier based on voltage
        tier_num = min(14, max(0, math.ceil(math.log(self.voltage / 8, 4))))
        return VoltageTier.from_tier_num(tier_num)
    
    @classmethod
    def from_tier(cls, tier: VoltageTier) -> 'Voltage':
        # Calculate voltage from tier
        voltage = 8 * (4 ** (tier.value))
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
