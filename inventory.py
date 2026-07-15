
from __future__ import annotations
from common import *


ITEM_WEIGHTS: dict[str, float] = {
    "iron": 2,

    "staff": 3,
    "bow": 2,

    "mace": 4,
    "sword": 2,
    "axe": 2,

    "musket": 2,

    "helmet": 1.5,
    "chestplate": 3,
    "arm pad": 1.5,
    "legging": 2,
    "shield": 3,

    "coin": 0,
    "ring": 0,

    "shuriken": 0.1,
    "bandage": 0.1,
    "used bandage": 0.1,
    "pill": 0.05,
    "flintlock bullet": 0.05,
    "musket bullet": 0.1,
    "arrow": 0.1,

    "magic staff": 3
}


class Inventory:

    def __init__(self, capacity: float = 20, items: dict[str, int] | None = None) -> None:
        self.capacity: float = capacity
        self.items: dict[str, int] = items if items is not None else {}
        if self.capacity > 0 and self.weight() > self.capacity: raise ValueError(f"Item weight exceeds capacity from the start")

    # valid python representation
    def __repr__(self) -> str: return f"Inventory({self.capacity}, {repr(self.items)})"

    # cleaner string for display
    def __str__(self) -> str:
        DISPLAY_INDENT: str = " " * 2
        default: str = "{"
        result: str = default
        counter: int = 0

        for item in self.items:
            result += f"\n{DISPLAY_INDENT}{item}: {self.items[item]}{',' if counter < len(self.items) - 1 else ''}"
            counter += 1
        return result + ("}" if result == default else (f"\n\n{DISPLAY_INDENT}Capacity: {self.weight()}/{self.capacity}\n}}" if self.capacity > 0 else "\n}"))

    # for saving data
    @staticmethod
    def save(target: Inventory) -> dict: return dict(target.items)

    # for loading data
    @staticmethod
    def load(data: dict) -> Inventory: return Inventory(data["capacity"], data["items"])
    
    # delete items with 0 or less quantity
    def cleanup(self) -> None:
        to_delete: list[str] = []
        for item in self.items:
            if self.items[item] <= 0: to_delete.append(item)
        for item in to_delete: self.items.pop(item)

    # NOTE TO SELF: DO NOT USE SELF.WEIGHT() TO CHECK IF INVENTORY IS EMPTY
    # COINS HAVE NO MASS
    def weight(self) -> float:
        self.cleanup()
        weight: float = 0
        for existing in self.items: weight += round((ITEM_WEIGHTS[existing] if existing in ITEM_WEIGHTS else 1) * self.items[existing], VALUE_ROUND)
        return round(weight, VALUE_ROUND)

    # USE THIS
    def is_empty(self) -> bool: return len(self.items) == 0
    
    def remove(self, item: str, quantity: int = 1) -> None:
        if quantity <= 0: raise InventoryError("Quantity must be positive")
        if not(item in self.items): raise InventoryError(f"{item} is not in this inventory")

        selected_qty: int = self.items[item]
        if quantity > selected_qty: raise InventoryError(f"Quantity too large ({quantity}); there's only {item_display(item, selected_qty)}")
        self.items[item] -= quantity
        self.cleanup()

    def add(self, item: str, quantity: int = 1) -> None:
        if quantity <= 0: raise InventoryError("Quantity must be positive")

        # don't have to call self.cleanup() because self.weight() calls it
        total: float = self.weight() + (ITEM_WEIGHTS[item] if item in ITEM_WEIGHTS else 1) * quantity
        if self.capacity > 0 and total > self.capacity: raise InventoryError(f"Not enough inventory capacity to add {item_display(item, quantity)} ({total}/{self.capacity})")
        self.items[item] = self.items[item] + quantity if item in self.items else quantity
