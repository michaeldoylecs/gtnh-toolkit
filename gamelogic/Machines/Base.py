from gamelogic.Items import ItemStack
from gamelogic.Electricity import VoltageTier
from gamelogic.GameTime import GameTime


class MachineRecipe():
    machine_name: str
    machine_tier: VoltageTier
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTime
    eu_per_gametick: int
