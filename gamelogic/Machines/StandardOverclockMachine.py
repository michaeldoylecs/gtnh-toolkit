import math
import math
from gamelogic.Electricity import Voltage, VoltageTier
from gamelogic.Items import ItemStack
# Update import:
from .Base import MachineRecipe
from gamelogic.GameTime import GameTime

class StandardOverclockMachineRecipe(MachineRecipe):

    def __init__(
            self,
            machine_name: str,
            machine_tier: VoltageTier,
            inputs: list[ItemStack],
            outputs: list[ItemStack],
            # Update type hint:
            duration: GameTime,
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
            # Update type hint:
            duration: GameTime,
            eu_per_gametick: int,
    # Update return type hint:
    ) -> tuple[GameTime, int]:
        recipe_voltage = Voltage(eu_per_gametick)
        if (machine_tier < recipe_voltage.tier):
            raise ValueError("Recipe tier cannot exceed machine tier.")
        elif (machine_tier == recipe_voltage.tier):
            return (duration, eu_per_gametick)

        OVERCLOCK_SPEED_FACTOR = 2.0
        OVERCLOCK_POWER_FACTOR = 4

        tier_difference = machine_tier.value - recipe_voltage.tier.value
        # Update duration calculation:
        original_ticks = duration.as_ticks()
        new_duration_ticks = math.ceil(max(1, original_ticks / (OVERCLOCK_SPEED_FACTOR ** tier_difference)))
        new_duration = GameTime.from_ticks(new_duration_ticks)
        new_eu_per_gametick = eu_per_gametick * (OVERCLOCK_POWER_FACTOR ** tier_difference)

        return (new_duration, new_eu_per_gametick)
