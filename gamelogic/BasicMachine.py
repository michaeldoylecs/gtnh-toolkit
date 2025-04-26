
from enum import Enum
import math
from typing import NewType

from gamelogic.Items import ItemStack

GameTicks = NewType('GameTicks', int)

class Voltage:
    def __init__(self, voltage: int):
        self.voltage = max(0, voltage)  # Ensure voltage is non-negative
    
    @property
    def tier(self) -> int:
        # Special case for 0 voltage
        if self.voltage == 0:
            return 1  # ULV tier
        
        # Calculate tier based on voltage
        return min(14, max(1, math.ceil(math.log(self.voltage / 8, 4))))
    
    @property
    def label(self) -> str:
        tier_labels = {
            1: "ULV",
            2: "MV",
            3: "HV",
            4: "EV",
            5: "IV",
            6: "LUV",
            7: "ZPM",
            8: "UV",
            9: "UHV",
            10: "UEV",
            11: "UIV",
            12: "UMV",
            13: "UXV",
            14: "MAX"
        }
        return tier_labels.get(self.tier, "UNDEFINED")
    
    @classmethod
    def from_tier(cls, tier: int) -> 'Voltage':
        if tier <= 0:
            return cls(0)
        
        # Calculate voltage from tier
        voltage = 8 * (4 ** (tier - 1))
        return cls(voltage)
    
    def __eq__(self, other):
        if isinstance(other, Voltage):
            return self.voltage == other.voltage
        return False
    
    def __repr__(self):
        return f"Voltage({self.voltage}, {self.label})"




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
            self.machine_voltage_tier,
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
        tier_ratio = recipe_voltage.tier / machine_voltage.tier
        speed_overclock = OVERCLOCK_SPEED_FACTOR**tier_ratio
        power_overclock = OVERCLOCK_POWER_FACTOR**tier_ratio

        recipe_time = GameTicks(math.ceil(duration / speed_overclock))
        recipe_cost = int(eu_per_gametick * power_overclock)
        return (recipe_time, recipe_cost)
