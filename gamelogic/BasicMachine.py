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


class StandardOverclockMachineRecipe(MachineRecipe):

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
        recipe_voltage = Voltage(eu_per_gametick)
        if (machine_tier < recipe_voltage.tier):
            raise ValueError("Recipe tier cannot exceed machine tier.")
        elif (machine_tier == recipe_voltage.tier):
            return (duration, eu_per_gametick)

        OVERCLOCK_SPEED_FACTOR = 2.0
        OVERCLOCK_POWER_FACTOR = 4
        
        tier_difference = machine_tier.value - recipe_voltage.tier.value
        new_duration = GameTicks(math.ceil(max(1, duration / (OVERCLOCK_SPEED_FACTOR ** tier_difference))))
        new_eu_per_gametick = eu_per_gametick * (OVERCLOCK_POWER_FACTOR ** tier_difference)

        return (new_duration, new_eu_per_gametick)


class PerfectOverclockMachineRecipe(MachineRecipe):

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

        recipe_time, recipe_cost = self.__apply_perfect_overclock(
            self.machine_tier,
            duration,
            eu_per_gametick
        )
        self.duration = recipe_time
        self.eu_per_gametick = recipe_cost


    def __apply_perfect_overclock(
            self,
            machine_tier: VoltageTier,
            duration: GameTicks,
            eu_per_gametick: int,
    ) -> tuple[GameTicks, int]:
        recipe_voltage = Voltage(eu_per_gametick)
        if (machine_tier < recipe_voltage.tier):
            raise ValueError("Recipe tier cannot exceed machine tier.")
        elif (machine_tier == recipe_voltage.tier):
            return (duration, eu_per_gametick)

        OVERCLOCK_SPEED_FACTOR = 4.0 
        OVERCLOCK_POWER_FACTOR = 4
        
        tier_difference = machine_tier.value - recipe_voltage.tier.value
        new_duration = GameTicks(math.ceil(max(1, duration / (OVERCLOCK_SPEED_FACTOR ** tier_difference))))
        new_eu_per_gametick = eu_per_gametick * (OVERCLOCK_POWER_FACTOR ** tier_difference)

        return (new_duration, new_eu_per_gametick)
