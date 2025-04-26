
from enum import Enum, auto
import math
from typing import NewType

from gamelogic.Items import ItemStack

GameTicks = NewType('GameTicks', int)

class VoltageTier(Enum):
    ULV = 1
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
    
    @classmethod
    def from_int(cls, tier_num: int) -> 'VoltageTier':
        tier_num = max(1, min(14, tier_num))
        return list(cls)[tier_num - 1]
    
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
        tier_num = min(14, max(1, math.ceil(math.log(self.voltage / 8, 4))))
        return VoltageTier.from_int(tier_num)
    
    @classmethod
    def from_tier(cls, tier: VoltageTier) -> 'Voltage':
        # Calculate voltage from tier
        voltage = 8 * (4 ** (tier.value - 1))
        return cls(voltage)
    
    def __eq__(self, other):
        if isinstance(other, Voltage):
            return self.voltage == other.voltage
        return False
    
    def __repr__(self):
        return f"Voltage({self.voltage}, {self.tier})"




class MachineRecipe():
    machine_name: str
    machine_voltage: Voltage
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int


class BasicMachineRecipe(MachineRecipe):

    def __init__(
            self,
            machine_name: str,
            machine_voltage: Voltage,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            duration: GameTicks,
            eu_per_gametick: int
    ):
        self.machine_name = machine_name
        self.machine_voltage = machine_voltage
        self.inputs = inputs
        self.outputs = outputs

        recipe_time, recipe_cost = self.__apply_standard_overclock(
            self.machine_voltage,
            duration,
            eu_per_gametick
        )
        self.duration = recipe_time
        self.eu_per_gametick = recipe_cost


    def __apply_standard_overclock(
            self,
            machine_voltage: Voltage,
            duration: GameTicks,
            eu_per_gametick: int,
    ) -> tuple[GameTicks, int]:
        OVERCLOCK_SPEED_FACTOR = 2.0
        OVERCLOCK_POWER_FACTOR = 4

        recipe_voltage = Voltage(eu_per_gametick)
        tier_ratio = recipe_voltage.tier.value / machine_voltage.tier.value
        speed_overclock = OVERCLOCK_SPEED_FACTOR**tier_ratio
        power_overclock = OVERCLOCK_POWER_FACTOR**tier_ratio

        recipe_time = GameTicks(math.ceil(duration / speed_overclock))
        recipe_cost = int(eu_per_gametick * power_overclock)
        return (recipe_time, recipe_cost)
