import math
from gamelogic.electricity import Voltage, VoltageTier
from gamelogic.items import ItemStack
from .base import MachineRecipe
from gamelogic.game_time import GameTime

class StandardOverclockMachineRecipe(MachineRecipe):

    def __init__(
            self,
            machine_name: str,
            machine_tier: VoltageTier,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            duration: GameTime,
            eu_per_gametick: Voltage
    ):
        self._machine_name = machine_name
        self._machine_tier = machine_tier
        self._inputs = inputs
        self._outputs = outputs

        recipe_time, recipe_cost = self.__apply_standard_overclock(
            self.machine_tier,
            duration,
            eu_per_gametick
        )
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

    def __apply_standard_overclock(
            self,
            machine_tier: VoltageTier,
            duration: GameTime,
            eu_per_gametick: Voltage,
    ) -> tuple[GameTime, Voltage]:
        recipe_voltage = eu_per_gametick
        if (machine_tier < recipe_voltage.tier):
            raise ValueError("Recipe tier cannot exceed machine tier.")
        elif (machine_tier == recipe_voltage.tier):
            return (duration, eu_per_gametick)

        OVERCLOCK_SPEED_FACTOR = 2.0
        OVERCLOCK_POWER_FACTOR = 4

        tier_difference = machine_tier.value - recipe_voltage.tier.value
        original_ticks = duration.as_ticks()
        new_duration_ticks = math.ceil(max(1, original_ticks / (OVERCLOCK_SPEED_FACTOR ** tier_difference)))
        new_duration = GameTime.from_ticks(new_duration_ticks)
        new_eu_per_gametick = eu_per_gametick * (OVERCLOCK_POWER_FACTOR ** tier_difference)

        return (new_duration, new_eu_per_gametick)
