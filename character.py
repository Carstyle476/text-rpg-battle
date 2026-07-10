
from __future__ import annotations
from exceptions import *
from inventory import *

# for single-weapon - dual-wield doubles bonus
# 2nd value in tuple is for determining required consumable
WEAPON_BONUSES: dict[str, tuple[float, str]] = {
    # rudimentary weapons
    "plank": (1, ""),
    "stone": (1, "stone"),
    "hammer": (2, ""),
    "boomerang": (2, ""),

    # weaker weapons
    "knife": (5, ""),
    "slingshot": (5, "stone"),
    "dagger": (10, ""),
    "nunchucks": (15, ""),
    "shuriken": (15, "shuriken"),
    "staff": (20, ""),
    
    # stronger weapons
    "mace": (30, ""),
    "sword": (35, ""),
    "axe": (40, ""),
    
    # old guns
    "flintlock": (60, "flintlock bullet"),
    "musket": (70, "musket bullet"),
    
    # magic!!!
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

HEALING_POTION_AMOUNT: float = 20
DEFAULT_INVENTORY_CAPACITY: int = 20
INFO_MENU_WIDTH: int = 38

# check if it exists
def check_weapon(weapon: str) -> bool: return weapon is "" or weapon in WEAPON_BONUSES
def check_armor(armor: str) -> bool: return armor is "" or armor in ARMOR_REDUCTIONS

class Character:

    def __init__(self, name: str, hp_cap: float, hp: float, strength: float, regen: float = 0, weapon: tuple[str, bool] | None = None, armor_set: set[str] | None = None, inventory: Inventory | None = None) -> None:
        if name is "": raise ValueError("You have to give every Character a name!")
        self.name: str = name
        
        self.hp_cap: float = hp_cap
        self.hp: float = hp_cap if hp < 0 or hp > hp_cap else hp
        self.strength: float = strength
        self.regen: float = regen
        
        self.weapon: tuple[str, bool] = weapon if weapon is not None else ("", False)
        if not(check_weapon(self.weapon[0])): raise EquipmentError(f"Weapon is not valid: {weapon}")
        self.armor_set: set[str] = armor_set if armor_set is not None else set()
        for armor in self.armor_set:
            if not(check_armor(armor)): raise EquipmentError(f"Armor piece is not valid: {armor}")
        
        self.inventory: Inventory = inventory if inventory is not None else Inventory(DEFAULT_INVENTORY_CAPACITY)
    
    # valid python representation (but it's all in 1 line so it's horrible)
    def __repr__(self) -> str:
        result: str = f"Character('{self.name}', {self.hp_cap}, {self.hp}, {self.strength}, {self.regen}, {self.weapon}, {{"
        counter: int = 0
        for armor in self.armor_set:
            result += f"'{armor}'{'' if counter < len(self.armor_set) - 1 else '}'}, "
            counter += 1
        return  result + repr(self.inventory) + ")"
    
    # admittedly MUCH more readable
    def __str__(self) -> str:
        armor_display = "\n"
        for armor in self.armor_set: armor_display += f"   - {armor}\n"
        if armor_display is "\n": armor_display = " None\n"
        
        result = f"""
{'CHARACTER INFO':^{INFO_MENU_WIDTH}}
{'=' * INFO_MENU_WIDTH}
  Name: {self.name}
  HP: {self.hp}/{self.hp_cap} HP
  Strength: {self.strength}
  Pending health regeneration: {self.regen} HP

  Current weapon: {self.weapon[0]}
   Dual-wielding: {'Yes' if self.weapon[1] else 'No'}

  Currently worn armor pieces:{armor_display}
  Inventory:
{str(self.inventory)}
"""
        return result
    
    # NOTE: self.inventory.remove can throw an InventoryError
    def equip_weapon(self, desired: str) -> None:
        if not(check_weapon(desired)): raise EquipmentError(f"Desired weapon is not valid: {desired}")

        old: tuple[str, bool] = (self.weapon[0], self.weapon[1])
        unequipped_first: bool = False
        replace: bool = old[0] is not desired
        print(replace)
        self.inventory.remove(desired)
        if replace:
            try:
                self.unequip_weapon()
                unequipped_first = True
                self.unequip_weapon()
            except InventoryError as e:
                # rollback if we cant store the 2nd old weapon
                if unequipped_first:
                    self.inventory.remove(old[0])
                    self.weapon = old
                raise e
        self.weapon = (desired, not(replace))

    def unequip_weapon(self) -> None:
        if self.weapon[0] is not "":
            weapon_name: str = self.weapon[0]
            self.inventory.add(self.weapon[0])
            if not(self.weapon[1]): weapon_name = ""
            self.weapon = (weapon_name, False)

    def equip_armor(self, desired: str) -> None:
        if not(check_armor(desired)): raise EquipmentError(f"Desired armor piece is not valid: {desired}")
        remove_count: int = 2 if ARMOR_REDUCTIONS[desired][1] else 1
        # remove armor piece from inventory if equipping
        self.inventory.remove(desired, remove_count)
        before: int = len(self.armor_set)
        self.armor_set.add(desired)
        if len(self.armor_set) is before: self.inventory.add(desired, remove_count)

    def unequip_armor(self, desired: str) -> None:
        if not(check_armor(desired)): raise EquipmentError(f"Desired armor piece is not valid: {desired}")
        try:
            self.armor_set.remove(desired)
            self.inventory.add(desired, 2 if ARMOR_REDUCTIONS[desired][1] else 1)
        except KeyError: raise EquipmentError(f"{desired} is not among currently worn armor set")
        except InventoryError as e:
            self.armor_set.add(desired)
            raise e
    
    # equip either a weapon or item
    def equip(self, desired: str) -> None:
        try: self.equip_weapon(desired)
        except (InventoryError, EquipmentError):
            try: self.equip_armor(desired)
            except (InventoryError, EquipmentError): raise EquipmentError(f"Could not equip {desired} in any way")

    def unequip(self, desired: str = "") -> None:
        if desired is "": self.unequip_weapon()
        else:
            try: self.unequip_armor(desired)
            except (InventoryError, EquipmentError): raise EquipmentError(f"Could not unequip {desired} in any way")
    
    # heal if the character has a healing potion
    # NOTE: self.inventory.remove can throw an InventoryError
    def heal(self) -> None:
        self.inventory.remove("healing potion")
        self.hp = min(self.hp_cap, self.hp + HEALING_POTION_AMOUNT)
        self.regen += HEALING_POTION_AMOUNT
        print(f"{self.name} heals for {HEALING_POTION_AMOUNT} HP and will regenerate {self.regen} more!\n(Pro tip: Stay passive on your next turn to regenerate more.)")

    # play this character's turn
    def turn(self, target: Character | None = None) -> None:
        attacking: bool = False
        if target is not None:
            if target is self: raise ValueError(f"{self.name} cannot attack itself")
            attacking = True

            # handle weapons that use other things (e.g. flintlocks and their bullets)
            consumable: str = "" if self.weapon[0] is "" else WEAPON_BONUSES[self.weapon[0]][1]
            consume_weapon: bool = False
            if consumable is not "":
                consumable_amt: int = self.inventory.quantity(consumable)
                if consumable_amt is 1 and self.weapon[1]:
                    if consumable is not self.weapon[0]: self.unequip_weapon()
                    else: consume_weapon = True
                if consumable_amt > 0: self.inventory.remove(consumable, min(2 if self.weapon[1] else 1, consumable_amt))
            
            damage: float = calculate_damage(self, target)
            target.hp -= damage
            if consume_weapon: self.weapon = ("", False)

            # i am NOT one-lining this bit of code
            weapon_display: str = ""
            if self.weapon[1]: weapon_display = f" with dual-wielding {self.weapon[0] + ('s' if self.weapon[0][-1] is not 's' else '')}"
            elif self.weapon[0] is not "": weapon_display = f" with a{'n' if self.weapon[0][0] in 'aeiou' else ''} {self.weapon[0]}"

            print(f"{self.name} attacks {target.name}{weapon_display} for {damage} damage!")
        
        # gain ability to regenerate more if passive
        # (game design is my passion!!!!!)
        to_regen: float = min(self.hp_cap - self.hp, self.regen * (2 if not(attacking) else 1))
        if to_regen > 0:
            print(f"{self.name}{' also' if attacking else ''} regenerates {to_regen} HP from a healing potion!")
            self.hp += to_regen
            self.regen -= min(to_regen, self.regen)


def calculate_damage(char_a: Character, char_b: Character) -> float:
    raw_damage: float = char_a.strength + (WEAPON_BONUSES[char_a.weapon[0]][0] if char_a.weapon[0] in WEAPON_BONUSES else 0) * (2 if char_a.weapon[1] else 1)
    armor_reduct: float = 0
    for armor in char_b.armor_set: armor_reduct += ARMOR_REDUCTIONS[armor][0]
    return round(raw_damage * max(0, 1 - armor_reduct), 3)
