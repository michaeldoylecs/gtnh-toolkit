from dataclasses import dataclass
from functools import cache


@dataclass(frozen=True)
class Item:
    name: str

@dataclass(frozen=True)
class ItemStack:
    item: Item
    quantity: float

@cache
def make_item(name: str) -> Item:
    return Item(name)

def make_itemstack(name: str, quantity: float) -> ItemStack:
    return ItemStack(make_item(name), quantity)
