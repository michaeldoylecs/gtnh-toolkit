from dataclasses import dataclass

from gamelogic.machines import MachineRecipe
from gamelogic.items import Item, make_item

@dataclass(frozen=True)
class TargetRate:
    item: Item
    quantity_per_second: float

@dataclass(frozen=True)
class FactoryConfig:
    recipes: list[MachineRecipe]
    targets: list[TargetRate]

def make_target(itemname: str, quantity: float) -> TargetRate:
    return TargetRate(make_item(itemname), quantity)
