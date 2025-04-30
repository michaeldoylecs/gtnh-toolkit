import math
from gamelogic.electricity import Voltage, VoltageTier
from gamelogic.items import ItemStack
from .base import MachineRecipe
from gamelogic.game_time import GameTime

class IndustrialCentrifugeRecipe(MachineRecipe):

    def __init__(
            self,
            machine_name: str,
            machine_tier: VoltageTier,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            duration: GameTime,
            eu_per_gametick: Voltage
    ):
        recipe_time, recipe_cost, parallels = self.__apply_overclock(
            machine_tier,
            duration,
            eu_per_gametick
        )
        self._machine_name = machine_name
        self._machine_tier = machine_tier
        self._inputs = [ItemStack(input.item, input.quantity * parallels) for input in inputs]
        self._outputs = [ItemStack(output.item, output.quantity * parallels) for output in outputs]
        self._duration = recipe_time
        self._eu_per_gametick = recipe_cost
    
    @property
    def machine_name(self) -> str:
        return self._machine_name

    @property
    def machine_tier(self) -> VoltageTier:
        return self._machine_tier
    
    @property
    def inputs(self) -> list[ItemStack]:
        return self._inputs
    
    @property
    def outputs(self) -> list[ItemStack]:
        return self._outputs
    
    @property
    def duration(self) -> GameTime:
        return self._duration
    
    @property
    def eu_per_gametick(self) -> Voltage:
        return self._eu_per_gametick


    def __apply_overclock(
            self,
            machine_tier: VoltageTier,
            duration: GameTime,
            eu_per_gametick: Voltage,
    ) -> tuple[GameTime, Voltage, int]:
        recipe_voltage = eu_per_gametick
        if (machine_tier < recipe_voltage.tier):
            raise ValueError("Recipe tier cannot exceed machine tier.")

        OVERCLOCK_SPEED_FACTOR = 4.0
        OVERCLOCK_POWER_FACTOR = 4

        speed_multiplier = 1.8
        eu_multiplier = 0.9
        max_parallels = machine_tier.value * 2

        parallels = min(max_parallels, machine_tier.max_voltage.voltage // (recipe_voltage.voltage * eu_multiplier * max_parallels))

        tier_difference = machine_tier.value - (recipe_voltage * parallels).tier.value
        original_ticks = duration.as_ticks()
        
        new_duration_ticks = math.ceil(max(1, original_ticks / (speed_multiplier * (OVERCLOCK_SPEED_FACTOR ** tier_difference))))
        new_duration = GameTime.from_ticks(new_duration_ticks)
        new_eu_per_gametick: Voltage = recipe_voltage * eu_multiplier * (OVERCLOCK_POWER_FACTOR ** tier_difference)

        return (new_duration, new_eu_per_gametick, parallels)
