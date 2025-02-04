from dataclasses import dataclass
from functools import cache
from typing import NewType

GameTicks = NewType('GameTicks', int)

@dataclass(frozen=True)
class Item:
    name: str

@dataclass(frozen=True)
class ItemStack:
    item: Item
    quantity: int

@dataclass(frozen=True)
class Recipe:
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int

@dataclass(frozen=True)
class MachineRecipe:
    machine_name: str
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int

@dataclass(frozen=True)
class TargetRate:
    item: Item
    quantity_per_second: float

@cache
def make_item(name: str) -> Item:
    return Item(name)
