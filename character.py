
from __future__ import annotations
from common import *
from inventory import Inventory


# for single-weapon - dual-wield doubles bonus
# 2nd value in tuple is for determining required consumable
WEAPON_BONUSES: dict[str, tuple[float, str]] = {
    # rudimentary weapons
    "stick": (1, ""),
    "stone": (1, "stone"),
    "boomerang": (2, ""),
    "glass bottle": (3, "glass bottle"),

    # weaker weapons
    "knife": (5, ""),
    "slingshot": (5, "stone"),
    "dagger": (10, ""),
    "nunchucks": (15, ""),
    "shuriken": (15, "shuriken"),
    "staff": (20, ""),
    "bow": (20, "arrow"),

    # stronger weapons
    "mace": (30, ""),
    "sword": (35, ""),
    "axe": (40, ""),

    # old guns
    "flintlock": (60, "flintlock bullet"),
    "musket": (70, "musket bullet"),

    # magic!!!
    "magic staff": (100, ""),
    "ring": (150, "")
}

# 1 = full reduction, pieces stack
# bool is for determining if it comes in pairs or not
ARMOR_REDUCTIONS: dict[str, tuple[float, bool]] = {
    "chestplate": (0.2, False),
    "shield": (0.2, False),
    "legging": (0.15, True),
    "helmet": (0.15, False),
    "arm pad": (0.1, True),
    "boot": (0.1, True)
}

HEALING_ITEMS: dict[str, tuple[float, str]] = {
    "healing potion": (40, "glass bottle"),
    "pill": (25, ""),
    "bandage": (10, "used bandage")
}

INFO_MENU_WIDTH: int = 38
INVALID_WEAPON: str = " not a weapon"
INVALID_ARMOR: str = " not an armor piece"

# check if it exists
def check_weapon(weapon: str) -> bool: return weapon == "" or weapon in WEAPON_BONUSES
def check_armor(armor: str) -> bool: return armor == "" or armor in ARMOR_REDUCTIONS


class Character:

    def __init__(self, name: str, hp_cap: float, hp: float, strength: float, regen: float = 0, weapon: tuple[str, bool] | None = None, armor_set: set[str] | None = None, inventory: Inventory | None = None) -> None:
        if name == "": raise ValueError("You have to give every Character a name!")
        self.name: str = name

        self.hp_cap: float = hp_cap
        self.hp: float = hp_cap if hp < 0 or hp > hp_cap else hp
        self.strength: float = strength
        self.regen: float = regen

        self.weapon: tuple[str, bool] = weapon if weapon is not None else ("", False)
        if not(check_weapon(self.weapon[0])): raise ValueError(f"{item_display(self.weapon[0], 1, True)}{INVALID_WEAPON}")
        self.armor_set: set[str] = armor_set if armor_set is not None else set()
        for armor in self.armor_set:
            if not(check_armor(armor)): raise ValueError(f"{item_display(armor + ('s' if ARMOR_REDUCTIONS[armor][1] else ''), 1, True)}{INVALID_ARMOR}")

        self.inventory: Inventory = inventory if inventory is not None else Inventory()

    # valid python representation (but it's all in 1 line so it's horrible)
    def __repr__(self) -> str: return f"Character('{self.name}', {self.hp_cap}, {self.hp}, {self.strength}, {self.regen}, {self.weapon}, {self.armor_set}, {repr(self.inventory)})"

    # admittedly MUCH more readable
    def __str__(self) -> str:
        armor_display = "\n"
        for armor in self.armor_set: armor_display += f"   - {armor + ('s' if ARMOR_REDUCTIONS[armor][1] else '')}\n"
        if armor_display == "\n": armor_display = " None\n"

        return f"""
{'CHARACTER INFO':^{INFO_MENU_WIDTH}}
{'=' * INFO_MENU_WIDTH}
  Name: {self.name}
  HP: {self.hp}/{self.hp_cap} HP
  Strength: {self.strength}
  Pending health regeneration: {self.regen} HP

  Current weapon: {self.weapon[0] if self.weapon[0] != '' else 'None'}
  Dual-wielding: {'Yes' if self.weapon[1] else 'No'}
  Currently worn armor pieces:{armor_display}
  Inventory:{'\n    ' if (self.inventory.is_empty()) else ' '}{str(self.inventory).replace('\n', '\n    ')}
"""

    # for saving to json-readable
    @staticmethod
    def save(target: Character) -> dict:
        return {
            "name": target.name,
            "hp_cap": target.hp_cap,
            "hp": target.hp,
            "strength": target.strength,
            "regen": target.regen,
            "weapon": tuple(target.weapon),
            "armor_set": list(target.armor_set), # apparently you can't convert a set to json
            "inventory": Inventory.save(target.inventory)
        }

    # for loading from json-readable
    @staticmethod
    def load(json_readable: dict) -> Character:
        if len(json_readable) != 8: raise ValueError("JSON-readable input does not seem to be of type Character")
        return Character(
            json_readable["name"],
            json_readable["hp_cap"],
            json_readable["hp"],
            json_readable["strength"],
            json_readable["regen"],
            tuple(json_readable["weapon"]),
            set(json_readable["armor_set"]),
            Inventory.load(json_readable["inventory"])
        )

    # equip a weapon
    # if nothing in hand, equip 1 copy, taking from inventory
    # if equipping same type as weapon already in-hand, dual-wield
    # if equipping different type, return old weapon(s) to inventory, take new weapon from inventory
    def equip_weapon(self, desired: str) -> None:
        if not(check_weapon(desired)): raise ValueError(f"{item_display(desired, 1, True)}{INVALID_WEAPON}")

        old: tuple[str, bool] = (self.weapon[0], self.weapon[1])
        unequipped_first: bool = False
        replace: bool = old[0] != desired
        self.inventory.remove(desired)
        if replace:
            try:
                self.unequip_weapon()
                unequipped_first = True
                self.unequip_weapon()
            except InventoryError as e:
                if unequipped_first:
                    self.inventory.remove(old[0])
                    self.weapon = old
                self.inventory.add(desired)
                raise e

        self.weapon = (desired, not(replace))

    # unequip a weapon
    # if nothing in hand, do nothing
    # if 1 weapon equipped, unequip it, adding it to inventory
    # if dual-wielding, unequip only one of them
    def unequip_weapon(self) -> None:
        if self.weapon[0] != "":
            weapon_name: str = self.weapon[0]
            self.inventory.add(self.weapon[0])
            if not(self.weapon[1]): weapon_name = ""
            self.weapon = (weapon_name, False)

    # equip an armor piece
    # if coming in pairs, take 2 from inventory
    # if no change was detected, rollback inventory take
    def equip_armor(self, desired: str) -> None:
        if not(check_armor(desired)): raise ValueError(f"{item_display(desired + ('s' if ARMOR_REDUCTIONS[desired][1] else ''), 1, True)}{INVALID_ARMOR}")

        remove_count: int = 2 if ARMOR_REDUCTIONS[desired][1] else 1
        self.inventory.remove(desired, remove_count)
        before: int = len(self.armor_set)
        self.armor_set.add(desired)

        if len(self.armor_set) == before: self.inventory.add(desired, remove_count)

    # unequip an armor piece
    # if not wearing it, do nothing
    # if coming in pairs, add 2 to inventory
    # if can't add, rollback state of "worn armor pieces" and complain
    def unequip_armor(self, desired: str) -> None:
        if not(check_armor(desired)): raise ValueError(f"{item_display(desired + ('s' if ARMOR_REDUCTIONS[desired][1] else ''), 1, True)}{INVALID_ARMOR}")
        try:
            self.armor_set.remove(desired)
            self.inventory.add(desired, 2 if ARMOR_REDUCTIONS[desired][1] else 1)
        except KeyError: return
        except InventoryError as e:
            self.armor_set.add(desired)
            raise e

    # heal with the selected item, removing it from inventory
    # if specified, replace it with another item
    # (e.g., you have a glass bottle after using a healing potion)
    def heal(self, item: str, regen: bool = False) -> None:
        if not(item in HEALING_ITEMS): raise ValueError(f"{item_display(item, 1, True)} not a healing item")

        self.inventory.remove(item)
        if HEALING_ITEMS[item][1] != "":
            try: self.inventory.add(HEALING_ITEMS[item][1])
            except InventoryError as e:
                self.inventory.add(item)
                raise e

        amount: float = HEALING_ITEMS[item][0]
        before_hp: float = self.hp
        self.hp = min(self.hp_cap, self.hp + amount * (3 if not(regen) else 1))
        if regen: self.regen += amount

        msg_suffix: str = '.' if not(regen) else f' and will regain {self.regen} more!\n(Pro tip: Defend on your next turn to regain more than usual)'
        print(f"\n{self.name} heals {self.hp - before_hp} HP{msg_suffix}")

    # play this character's turn
    # if target is specified, check it
    # if it's itself, complain
    # if not, handle weapon's consumables
    #
    # to handle weapon's consumables (if any):
    # determine how many consumables are used
    # if 0 consumables left:
    # - if consumes self: consume weapon, dual-wielding or not, after attacking
    # - else: complain
    # elif 1 consumable left and dual wielding:
    # - if consumes self: consume 1 from wield along with inventory
    # - else: forcibly single-wield, returning 1 weapon to inventory, before attacking
    # else: you're fine
    #
    # deal half the damage if the target is defending itself
    def turn(self, target: Character | None = None, target_defending: bool = False) -> None:
        attacking: bool = False

        if target is not None:
            if target == self: raise ValueError(f"{self.name} cannot attack itself")
            attacking = True

            # handle weapons that use other things (e.g. flintlocks and their bullets)
            consumable: str = "" if self.weapon[0] == "" else WEAPON_BONUSES[self.weapon[0]][1]
            consuming_self: bool = consumable == self.weapon[0]
            consume_weapon_amt: int = 0

            cut: int = 2 if self.weapon[1] else 0
            weapon_display: str = item_display(self.weapon[0], cut, True)[cut:]
            if consumable != "":
                consumable_display: str = item_display(consumable, 2 if self.weapon[1] else 1).lower()

                if not(consuming_self): print(f"\n{self.name}'s {weapon_display} going to use {consumable_display}!")
                consumable_amt: int = self.inventory.items[consumable]
                if consumable_amt == 0:
                    if consuming_self: consume_weapon_amt = 2 if self.weapon[1] else 1
                    else: raise InventoryError(f"{self.name}'s {weapon_display} out of {item_display(consumable, 2)[2:]}")
                elif consumable_amt == 1 and self.weapon[1]:
                    if consuming_self: consume_weapon_amt = 1
                    else:
                        self.unequip_weapon()
                        print(f"\n{self.name} is falling back to single-wield because only 1 {item_display(consumable, 0, True)} left!")
                if consumable_amt > 0: self.inventory.remove(consumable, min(2 if self.weapon[1] else 1, consumable_amt))

            damage: float = calculate_damage(self, target) / (2 if target_defending else 1)
            target.hp -= damage
            target.hp = round(target.hp, VALUE_ROUND)

            # i am NOT one-lining this bit of code
            if self.weapon[1]: weapon_display = f" with dual-wielding {self.weapon[0] + ('s' if self.weapon[0][-1] != 's' else '')}"
            elif self.weapon[0] != "": weapon_display = f" with a{'n' if self.weapon[0][0] in 'aeiou' else ''} {self.weapon[0]}"
            print(f"\n{self.name} attacks {target.name}{weapon_display} for {damage} damage!")

            if consume_weapon_amt == 2: self.weapon = ("", False)
            elif consume_weapon_amt == 1:
                weapon_name: str = self.weapon[0]
                self.unequip_weapon()
                self.inventory.remove(weapon_name)
            if consume_weapon_amt > 0: print(f"\n{self.name} used 1 or more weapon(s) from wield!")


        # gain ability to regenerate more if defending (not attacking)
        # (game design is my passion!!!!!)
        to_regen: float = min(self.hp_cap - self.hp, self.regen * (2 if not(attacking) else 1))
        if to_regen > 0:
            print(f"\n{self.name}{' also' if attacking else ''} regains {to_regen} HP!")
            self.hp += to_regen
            self.regen -= min(to_regen, self.regen)


def calculate_damage(char_a: Character, char_b: Character) -> float:
    raw_damage: float = char_a.strength + (WEAPON_BONUSES[char_a.weapon[0]][0] if char_a.weapon[0] in WEAPON_BONUSES else 0) * (2 if char_a.weapon[1] else 1)
    armor_reduct: float = 0
    for armor in char_b.armor_set: armor_reduct += ARMOR_REDUCTIONS[armor][0]
    return round(raw_damage * max(0, 1 - armor_reduct), VALUE_ROUND)
