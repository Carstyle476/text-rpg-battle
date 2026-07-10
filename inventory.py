
from exceptions import *

ITEM_WEIGHTS: dict[str, float] = {
    "plank": 2,
    
    "shuriken": 0.1,
    "staff": 3,
    
    "mace": 4,
    "sword": 2,
    "axe": 2,
    
    "helmet": 1.5,
    "chestplate": 3,
    "arm pad": 1.5,
    "legging": 2,
    
    "coin": 0,
    
    "flintlock bullet": 0.1,
    "musket bullet": 0.2
}

# inventory class: stores items and their quantities while taking their weights into account
class Inventory:

    def __init__(self: object, capacity: float, items: dict[str, int] = {}) -> object:
        self.capacity: float = capacity
        self.items: dict[str, int] = items
        self.cleanup()

    # valid python representation
    def __repr__(self: object) -> str:
        result: str = f"Inventory({self.capacity}" + "{"
        for item in self.items: result += "{item}: {self.items[item]}, "
        return result + "})"

    # cleaner string for display
    def __str__(self: object) -> str:
        result: str = "{"
        for item in self.items: result += f"\n  {item}: {self.items[item]},"
        return f"{result}{'\n' if result != '{' else ''}" + "}"
    
    # delete items with 0 or less quantity
    def cleanup(self: object) -> None:
        to_delete: list[str] = []
        for item in self.items:
            if self.items[item] <= 0: to_delete.append(item)
        for item in to_delete: self.items.pop(item)

    def quantity(self: object, item: str) -> int:
        self.cleanup()
        try: return self.items[item]
        except KeyError: raise InventoryError(f"{item} not in inventory")
    
    def remove(self: object, item: str, quantity: int = 1) -> None:
        selected_qty: int = self.quantity(item)
        if quantity > selected_qty: raise InventoryError(f"Quantity too large: {quantity}, only {selected_qty} of {item} exist")
        self.items[item] -= quantity
        self.cleanup()

    def add(self: object, item: str, quantity: int = 1) -> None:
        self.cleanup()
        weight: float = (ITEM_WEIGHTS[item] if item in ITEM_WEIGHTS else 1) * quantity
        for existing in self.items:
            weight += (ITEM_WEIGHTS[existing] if existing in ITEM_WEIGHTS else 1) * self.items[existing]
        if weight > self.capacity: raise InventoryError(f"Not enough inventory capacity to add {quantity} of {item}")
        if item in self.items: self.items[item] += quantity
        else: self.items.setdefault(item, quantity)
