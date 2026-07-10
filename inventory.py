
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

DISPLAY_INDENT: int = 3

# inventory class: stores items and their quantities while taking their weights into account
class Inventory:

    def __init__(self, capacity: float, items: dict[str, int] | None = None) -> None:
        self.capacity: float = capacity
        self.items: dict[str, int] = items if items is not None else {}
        self.cleanup()

    # valid python representation
    def __repr__(self) -> str:
        default: str = f"Inventory({self.capacity}, {{"
        result: str = default
        counter: int = 0
        for item in self.items:
            result += f"'{item}': {self.items[item]}{', ' if counter < len(self.items) - 1 else '}'}"
            counter += 1
        return (default + "}" if result is default else result) + ")"

    # cleaner string for display
    def __str__(self) -> str:
        default: str = " " * DISPLAY_INDENT + "{"
        result: str = default
        counter: int = 0
        for item in self.items:
            result += f"\n{" " * (DISPLAY_INDENT + 1)}{item}: {self.items[item]}{',' if counter < len(self.items) - 1 else ''}"
            counter += 1
        return f"{result}{'\n' + " " * DISPLAY_INDENT if result is not default else ''}}}"
    
    # delete items with 0 or less quantity
    def cleanup(self) -> None:
        to_delete: list[str] = []
        for item in self.items:
            if self.items[item] <= 0: to_delete.append(item)
        for item in to_delete: self.items.pop(item)

    def quantity(self, item: str) -> int:
        self.cleanup()
        return 0 if not(item in self.items) else self.items[item]
    
    def remove(self, item: str, quantity: int = 1) -> None:
        if quantity <= 0: raise InventoryError("Quantity argument must be positive")
        selected_qty: int = self.quantity(item)
        if quantity > selected_qty: raise InventoryError(f"Quantity too large: {quantity}, only {selected_qty} of {item} exist")
        self.items[item] -= quantity
        self.cleanup()

    def add(self, item: str, quantity: int = 1) -> None:
        if quantity <= 0: raise InventoryError("Quantity argument must be positive")
        self.cleanup()
        weight: float = (ITEM_WEIGHTS[item] if item in ITEM_WEIGHTS else 1) * quantity
        for existing in self.items:
            weight += (ITEM_WEIGHTS[existing] if existing in ITEM_WEIGHTS else 1) * self.items[existing]
        if weight > self.capacity: raise InventoryError(f"Not enough inventory capacity to add {quantity} of {item}")
        if item in self.items: self.items[item] += quantity
        else: self.items.setdefault(item, quantity)
