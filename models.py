from dataclasses import dataclass
from functools import cache
from typing import NewType

from machines.BasicMachine import MachineRecipe

GameTicks = NewType('GameTicks', int)

@dataclass(frozen=True)
class Item:
    name: str

@dataclass(frozen=True)
class ItemStack:
    item: Item
    quantity: float

@dataclass(frozen=True)
class Recipe:
    machine_name: str
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int

@dataclass(frozen=True)
class OverclockedRecipe:
    machine_name: str
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int

@dataclass(frozen=True)
class TargetRate:
    item: Item
    quantity_per_second: float

@dataclass(frozen=True)
class FactoryConfig:
    recipes: list[MachineRecipe]
    targets: list[TargetRate]

@cache
def make_item(name: str) -> Item:
    return Item(name)

def make_itemstack(name: str, quantity: float) -> ItemStack:
    return ItemStack(make_item(name), quantity)

def make_target(itemname: str, quantity: float) -> TargetRate:
    return TargetRate(make_item(itemname), quantity)
