
from exceptions import *
from inventory import *

# for single-weapon - dual-wield doubles bonus
# 2nd value in tuple is for determining required consumable
WEAPON_BONUSES: dict[str, tuple[float, str]] = {
    # rudimentary weapons
    "plank": (2, ""),
    "hammer": (2, ""),

    # weaker weapons
    "dagger": (5, ""),
    "boomerang": (5, ""),
    "knife": (10, ""),
    "nunchuck": (15, ""),
    "shuriken": (15, "shuriken"),
    "staff": (20, ""),
    
    "mace": (30, ""),
    "sword": (35, ""),
    "axe": (40, ""),
    
    "flintlock": (60, "flintlock bullet"),
    "musket": (70, "musket bullet"),
    
    "magic staff": (100, "")
}

# 1 = full reduction, pieces stack
# bool is for determining if it comes in pairs or not
ARMOR_REDUCTIONS: dict[str, tuple[float, bool]] = {
    "helmet": (0.15, False),
    "chestplate": (0.2, False),
    "arm pad": (0.1, True),
    "legging": (0.15, True),
    "boot": (0.1, True)
}

# check if it exists
def check_weapon(weapon: str) -> bool: return weapon == "" or weapon in WEAPON_BONUSES
def check_armor(armor: str) -> bool: return armor == "" or armor in ARMOR_REDUCTIONS

class Character:

    def __init__(self: object, name: str, hp_cap: float, strength: float, regen: float = 0, weapon: list[str, bool] = ["", False], armor_set: set[str] = set(), inventory: Inventory = Inventory(20)) -> object:
        self.name: str = name
        
        self.hp_cap: float = hp_cap
        self.hp: float = hp_cap
        self.strength: float = strength
        self.regen: float = regen
        
        if not(check_weapon(weapon[0])): raise EquipmentError(f"Weapon is not valid: {weapon[0]}")
        self.weapon: list[str, bool] = weapon
        for armor in armor_set:
            if not(check_armor(armor)): raise EquipmentError(f"Armor piece is not valid: {armor}")
        self.armor_set: set[str] = armor_set
        
        self.inventory: Inventory = inventory
    
    def equip_weapon(self: object, desired: str) -> None:
        if not(check_weapon(desired)): raise EquipmentError(f"Desired weapon is not valid: {desired}")

        replace: bool = self.weapon[0] != desired
        if replace:
            # try to switch weapons
            self.inventory.remove(desired)
            try: self.unequip_weapon()
            except InventoryError as e:
                self.inventory.add(desired)
                raise e
        else: self.inventory.remove(desired)

        self.weapon[1] = not(replace)
        self.weapon[0] = desired

    def unequip_weapon(self: object) -> None:
        if self.weapon[0] != "":
            self.inventory.add(self.weapon[0])
            if not(self.weapon[1]): self.weapon[0] = ""
            self.weapon[1] = False

    def equip_armor(self: object, desired: str) -> None:
        if not(check_armor(desired)): raise EquipmentError(f"Desired armor piece is not valid: {desired}")
        remove_count: int = 2 if ARMOR_REDUCTIONS[desired][1] else 1
        # remove armor piece from inventory if equipping
        self.inventory.remove(desired, remove_count)
        before: int = len(self.armor_set)
        self.armor_set.add(desired)
        if len(self.armor_set) == before: self.inventory.add(desired, remove_count)

    def unequip_armor(self: object, desired: str) -> None:
        if not(check_armor(desired)): raise EquipmentError(f"Desired armor piece is not valid: {desired}")
        try:
            self.armor_set.remove(desired)
            self.inventory.add(desired, 2 if ARMOR_REDUCTIONS[desired][1] else 1)
        except KeyError: raise EquipmentError(f"{desired} is not among currently worn armor set")
        except InventoryError as e:
            self.armor_set.add(desired)
            raise e

    def equip(self: object, desired: str) -> None:
        try: self.equip_weapon(desired)
        except (InventoryError, EquipmentError):
            try: self.equip_armor(desired)
            except (InventoryError, EquipmentError): raise EquipmentError(f"Could not equip {desired} in any way")

    def unequip(self: object, desired: str = "") -> None:
        if desired == "": self.unequip_weapon()
        else: self.unequip_armor(desired)
    
    # play this character's turn
    def turn(self: object, target: object = None) -> None:
        if target != None:
            consumable: str = "" if self.weapon[0] == "" else WEAPON_BONUSES[self.weapon[0]][1]
            consume_weapon: bool = False
            if consumable != "":
                consumable_amt: int = 0
                try: consumable_amt = self.inventory.items[consumable]
                except KeyError: raise EquipmentError(f"{consumable} consumable for {self.weapon[0]} weapon not in inventory")
                if consumable_amt == 1 and self.weapon[1]:
                    if consumable != self.weapon[0]: self.unequip_weapon()
                    else: consume_weapon = True
                self.inventory.remove(consumable, min(2, consumable_amt))
            target.hp -= calculate_damage(self, target)
            if consume_weapon:
                raise Warning("Weapon was used! Equip something else!")
                self.weapon[0] = ""
                self.weapon[1] = False
        # gain ability to regenerate more if passive
        to_regen: float = min(self.hp_cap - self.hp, self.regen * (2 if target == None else 1))
        self.hp += to_regen
        self.regen -= min(to_regen, self.regen)

def calculate_damage(char_a: Character, char_b: Character) -> float:
    raw_damage: float = char_a.strength + (WEAPON_BONUSES[char_a.weapon[0]][0] if char_a.weapon[0] in WEAPON_BONUSES else 0) * (2 if char_a.weapon[1] else 1)
    armor_reduct: float = 0
    for armor in char_b.armor_set: armor_reduct += ARMOR_REDUCTIONS[armor][0]
    return raw_damage * max(0, 1 - armor_reduct)
