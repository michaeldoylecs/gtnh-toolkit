
from enum import Enum
import math
from typing import NewType

from gamelogic.Items import ItemStack

GameTicks = NewType('GameTicks', int)

class VoltageTier(Enum):
    UNDEFINED = -1
    ULV = 1
    LV  = 1
    MV  = 2
    HV  = 3
    EV  = 4
    IV  = 5
    LUV = 6
    ZPM = 7
    UV  = 8
    UHV = 9
    UEV = 10
    UIV = 11
    UMV = 12
    UXV = 13
    MAX = 14


class VoltageLabel(Enum):
    UNDEFINED = -1
    ULV = 8
    LV  = 32
    MV  = 128
    HV  = 512
    EV  = 2048
    IV  = 8192
    LUV = 32768
    ZPM = 131072
    UV  = 524288
    UHV = 2097152
    UEV = 8388608
    UIV = 33554432
    UMV = 134217728
    UXV = 536870912
    MAX = 2147483648


def get_voltage_tier(voltage: int) -> VoltageTier:
    # Negative voltages are invalid.
    if voltage < 0:
        return VoltageTier.UNDEFINED
  
    # Special case, because we cannot take the log of 0.
    if voltage == 0:
        return VoltageTier.ULV

    tier_num = math.ceil(math.log(voltage / 8, 4))
    return VoltageTier(tier_num)


# Replace the above Voltage enums and functions with a dedicated Voltage class that that stores an integer voltage and returns a string label based on the voltage number AI!


class MachineRecipe():
    machine_name: str
    machine_voltage_tier: VoltageTier
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int


class BasicMachineRecipe(MachineRecipe):

    def __init__(
            self,
            machine_name: str,
            machine_voltage_tier: VoltageTier,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            duration: GameTicks,
            eu_per_gametick: int
    ):
        self.machine_name = machine_name
        self.machine_voltage_tier = machine_voltage_tier
        self.inputs = inputs
        self.outputs = outputs

        recipe_time, recipe_cost = self.__apply_standard_overclock(
            self.machine_voltage_tier,
            duration,
            eu_per_gametick
        )
        self.duration = recipe_time
        self.eu_per_gametick = recipe_cost


    def __apply_standard_overclock(
            self,
            machine_tier: VoltageTier,
            duration: GameTicks,
            eu_per_gametick: int,
    ) -> tuple[GameTicks, int]:
        OVERCLOCK_SPEED_FACTOR = 2.0
        OVERCLOCK_POWER_FACTOR = 4

        recipe_tier = get_voltage_tier(eu_per_gametick)
        tier_ratio = recipe_tier.value / machine_tier.value
        speed_overclock = OVERCLOCK_SPEED_FACTOR**tier_ratio
        power_overclock = OVERCLOCK_POWER_FACTOR**tier_ratio

        recipe_time = GameTicks(math.ceil(duration * speed_overclock))
        recipe_cost = eu_per_gametick * power_overclock
        return (recipe_time, recipe_cost)
