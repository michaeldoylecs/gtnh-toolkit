from typing import NewType
from gamelogic.Items import ItemStack
from gamelogic.Electricity import VoltageTier

GameTicks = NewType('GameTicks', int)

class MachineRecipe():
    machine_name: str
    machine_tier: VoltageTier # Changed from machine_voltage to machine_tier
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int
