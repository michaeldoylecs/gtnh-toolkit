import math
from typing import NewType
from gamelogic.Electricity import Voltage, VoltageTier
from gamelogic.Items import ItemStack

GameTicks = NewType('GameTicks', int)

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
            machine_tier: VoltageTier,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            duration: GameTicks,
            eu_per_gametick: int
    ):
        self.machine_name = machine_name
        self.machine_tier = machine_tier
        self.inputs = inputs
        self.outputs = outputs

        recipe_time, recipe_cost = self.__apply_standard_overclock(
            self.machine_tier,
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

        recipe_voltage = Voltage(eu_per_gametick)
        tier_ratio = recipe_voltage.tier.value / machine_tier.max_voltage
        speed_overclock = OVERCLOCK_SPEED_FACTOR**tier_ratio
        power_overclock = OVERCLOCK_POWER_FACTOR**tier_ratio

        recipe_time = GameTicks(math.ceil(duration / speed_overclock))
        recipe_cost = int(eu_per_gametick * power_overclock)
        return (recipe_time, recipe_cost)
