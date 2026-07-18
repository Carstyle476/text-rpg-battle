
from common import *
from character import Character, WEAPON_BONUSES, ARMOR_REDUCTIONS, HEALING_ITEMS
from inventory import Inventory
from data import *

from json import dumps, loads, JSONDecodeError
from random import random, randint
from time import sleep
from typing import Callable
from pathlib import Path


EXTENSION: str = ".save" # NOTE: DO NOT MAKE THIS BLANK OR ELSE THE LOAD SYSTEM WILL BREAK
PASSIVE_HEAL: int = 5

RAND_ENCOUNTER_MAX_LOOSE: int = 3 # i call this a "loose requirement", swarm enemies can push over this limit
RAND_ENCOUNTER_MAX_ACTUAL: int = 5 # the ACTUAL requirement

CHOOSE_WEAPON_CHANCE: float = 0.15 # per weapon, move to next if it lands "false"
CHOOSE_WEAPON_LIMIT: int = 13 # how far down the list it can go
DUAL_WIELD_CHANCE: float = 0.15

APPLY_ARMOR_CHANCE: float = 0.1 # per armor piece

ENCOUNTER_CHANCE_LOW: float = 0.15
ENCOUNTER_CHANCE_HIGH: float = 0.3

DEATH_THRESHOLD: float = 1

# every encounter is tracked, the more you survive, the harder the enemies get
ENCOUNTER_SCALING: float = 0.01
ENCOUNTER_SCALING_LIMIT: float = 0.1


def drops(drop_list: list[tuple[str, int, float]], capacity: int = 20) -> Inventory:
    result: Inventory = Inventory(capacity)

    for drop in drop_list:
        count: int = 0
        while random() < drop[2] and count < drop[1]: count += 1
        try: result.add(drop[0], count)
        except InventoryError: continue

    return result


# get int input for options (the main method of playing the game)
# no fancy text commands, sorry about that
def get_input(ask: str, options: list[str]) -> int:
    amt: int = len(options)
    
    while True:
        print(ask)
        for i in range(amt): print(f"{str(i).ljust(len(str(amt - 1)))} - {options[i]}")        
        raw: str = input("\n").strip()

        if raw != "" and raw.isdigit():
            num: int = int(raw)
            if num < amt: return num
        print("\nInvalid input, try again...")


# save/load game state
# true = all good
# false = not good
def save(state: dict, file: str, dont_ask: bool = False) -> bool:
    saveable: dict = dict(state)
    saveable["player"] = Character.save(saveable["player"])
    try:
        with open(file, mode = "x") as save_file: save_file.write(dumps(saveable))
    except FileExistsError:
        if dont_ask or input("\nSave file already exists\nDo you want to overwrite it? (y/n)\n>>> ").lower().strip() == "y":
            with open(file, mode = "w") as save_file: save_file.write(dumps(saveable))
            return True
        return False
    except OSError as e:
        print(f"\nCould not save file\n{repr(e)}")
        return False
    return True

def load(file: str) -> dict:
    with open(file, mode = "r") as save_file:
        loaded: dict = loads(save_file.read())
        loaded["player"] = Character.load(loaded["player"])
        loaded["dont encounter"] = True
        loaded["dont visit"] = True
        return loaded

def load_menu() -> dict:
    CANCEL: str = "Cancel"
    while True:
        options: list[str] = [str(file) for file in Path().glob(f"*{EXTENSION}")]
        options.insert(0, CANCEL)
        name: str = options[get_input("\nSelect a file to load:\n", options)]
        if name == CANCEL: return {"retry": True}
        try: return load(name)
        except JSONDecodeError: print("\nSave file is corrupted, please make a new save")
        except OSError as e: print(f"\nCould not load file\n{repr(e)}")


# if this returns negative then cancel whatever it's for
def get_positive_num(ask: str) -> int:
    while True:
        raw: str = input(ask).strip()
        if raw == "": return -1
        if raw.isdigit(): return int(raw)
        print("\nInvalid input, try again...")


def enemy_display(enemy: Character, indent: int) -> str:
    indent_str: str = " " * indent
    result: str = f"""{enemy.name}  ({enemy.hp}/{enemy.hp_cap} HP, {enemy.regen} regen HP)
{indent_str}Strength: {enemy.strength}
{indent_str}Weapon: {item_display(enemy.weapon[0], 1 + enemy.weapon[1]) if enemy.weapon[0] != '' else 'None'}
{indent_str}Armor:"""
    counter: int = 0
    for armor in enemy.armor_set:
        result += f"\n{indent_str}- {item_display(armor + ('s' if ARMOR_REDUCTIONS[armor][1] else ''), 1)}"
        counter += 1
    if counter == 0: result += " None"
    return result


def lose(name: str) -> dict:
    sleep(1)
    print(
"""
===============
  YOU'RE DEAD
===============
Reloading save...
"""
    )
    sleep(2)
    return load(f"{name}{EXTENSION}")


# main menu
# returns game state
def menu(welcome: bool = True) -> dict:
    print(
f"""
=============
  MAIN MENU 
============={'\nWelcome to the game!' if welcome else ''}
"""
    )
    
    choice: int = get_input(
        "Select an option:\n",
        [
            "Exit",
            "New game",
            "Load game",
            "How to play?"
        ]
    )

    if choice == 1:
        name: str = ""
        while name == "":
            name = input("\nWhat's your name, traveller?\n(leave blank to cancel)\n>>> ").strip()
            if name == "": return {"retry": True}
        
        new_game: dict = {
            "player": Character(name, 100, 100, 10),
            "px": 0,
            "py": len(WORLD_MAP.split("\n")) - 1,
            "search_x": -1,
            "search_y": -1,
            "encounter": 0,
            "autosave": input("\nDo you want to enable autosave?\nEvery action will be saved automatically without asking (y/n)\n>>> ").lower().strip() == "y",
            "dont encounter": True, # dont trigger random encounters
            "dont visit": False, # dont automatically visit places
            "visited bandits": False, # for showing bandits on the map legend
            "first": True, # first start (new save)
            "finished boss": False, # boss finished, trigger final dialog
            "actually finished": False # final dialog is finished, can't defeat boss again
        }

        successful: bool = save(new_game, f"{name}{EXTENSION}", False)
        if not(successful): return {"retry": True}
        return new_game
    if choice == 2: return load_menu()
    if choice == 3:
        print(
"""
This is a rather simple game, so this "tutorial" (more like clarification) won't be very long

Menus will have numbered options, all you have to do is select the option you want
by typing in that option's number

Some menus allow you to cancel the operation (either a whole separate option or just "leave blank")

You can dual-wield weapons by equipping 2 of the same kind
(e.g., equip a knife, then get another knife and equip that one, now you have 2 knives)

If you are about to overwrite your save file, the game will ask you
To confirm, type 'y' (without the quotes)
Any other answer will lead to the game not overwriting the file

In the game world, you can use the 0 option "Search area" to look for items around you
Sometimes, you can come across useful items

"Bugs" that are actually design choices:
- You can loot in the middle of battle
- I will add more to this list once I remember
"""
        )
        input("Hit enter to continue\n")
        return {"retry": True}
    return {}


# options menu
# blank dict - quit to menu
# same dict - back to game
# different dict - load that
def options(state: dict) -> dict:
    choice: int = -1
    while choice != 4:
        print(
"""
===========
  OPTIONS
===========
Game settings
"""
        )
        
        choice = get_input(
            "Select an option:\n",
            [
                "Quit to menu",
                "Save game",
                "Load game",
                f"Toggle autosave (currently {'on' if state['autosave'] else 'off'})",
                "Back to game"
            ]
        )
    
        if choice == 0: return {}
        if choice == 1: save(state, f"{state['player'].name}{EXTENSION}")
        if choice == 2:
            attempt: dict = load_menu()
            if not("retry" in attempt): return attempt
        if choice == 3:
            state["autosave"] = not(state["autosave"])
            save(state, f"{state['player'].name}{EXTENSION}", state["autosave"])

    return state


# inventory management menu
def manage(player: Character, outside: Inventory | None = None, in_battle: bool = False) -> None:
    ADD: str = "Add"
    DISCARD: str = "Discard"
    EQUIP: str = "Equip"
    UNEQUIP: str = "Unequip"
    HEAL: str = "Heal"
    DONE: str = "Done"
    INVALID: str = "You can't do that\n"
    
    if outside is None: outside = Inventory(capacity = -1)

    msg: str = ""
    while True:
        options: list[str] = [DONE]
        ADD_WITH_ITEMS: str = ADD

        if not(outside.is_empty()):
            ADD_WITH_ITEMS += f"\n{outside}".replace("\n", "\n    ")
            options.append(ADD_WITH_ITEMS)

        if not(player.inventory.is_empty()):
            options.append(DISCARD)
            for item in player.inventory.items:
                if item in HEALING_ITEMS and not(HEAL in options): options.append(HEAL)
                if (item in WEAPON_BONUSES or item in ARMOR_REDUCTIONS) and not(EQUIP in options or UNEQUIP in options):
                    options.append(EQUIP)
                    options.append(UNEQUIP)

        if (player.weapon[0] != "" or len(player.armor_set) > 0) and not(UNEQUIP in options): options.append(UNEQUIP)

        print(f"""
========================
  INVENTORY MANAGEMENT
========================
Manage your inventory, health, and weapons
{player}
{msg}"""
        )

        msg = ""
        choice_name: str = options[get_input("Select an option:\n", options)]
        if choice_name == DONE: return
        else:
            count: int = 0
            equip_weapon: bool = False

            outside_options: list[str] = list(outside.items)
            inside_options: list[str] = list(player.inventory.items)

            if choice_name == EQUIP or choice_name == UNEQUIP:
                skip: bool = False
                while True:
                    un: str = "E" if choice_name == EQUIP else "Une"
                    raw: str = input(f"\nSelect an option (leave blank to cancel):\n\n0 - {un}quip a weapon\n1 - {un}quip (an) armor piece(s)\n\n").strip()
                    if raw == "":
                        skip = True
                        break
                    if raw == "0" or raw == "1":
                        equip_weapon = raw == "0"
                        break
                    print("\nInvalid input, try again\n")
                if skip: continue
                if choice_name == UNEQUIP: inside_options.clear()

            # delete options accordingly
            in_op_deletes: list[str] = []
            for item in inside_options:
                delete_equip: bool = choice_name == EQUIP and not(equip_weapon and item in WEAPON_BONUSES or not(equip_weapon) and item in ARMOR_REDUCTIONS)
                if delete_equip or choice_name == HEAL and not(item in HEALING_ITEMS): in_op_deletes.append(item)
            for to_delete in in_op_deletes: inside_options.remove(to_delete)

            correct_options: list[str] = outside_options if choice_name == ADD_WITH_ITEMS else inside_options
            if choice_name == UNEQUIP:
                if not(equip_weapon):
                    for armor in player.armor_set: correct_options.append(armor)
                elif player.weapon[0] != "": correct_options.append(player.weapon[0])

            if len(correct_options) == 0:
                msg = INVALID
                continue
            CANCEL: str = "Cancel"
            correct_options.insert(0, CANCEL)
            item: str = correct_options[get_input("\nSelect an option (or cancel):\n", correct_options)]
            if item == CANCEL: continue
            selected_inventory: Inventory = outside if choice_name == ADD_WITH_ITEMS else player.inventory
            # VERY dodgy one-liner
            count: int = 1 if choice_name in [EQUIP, UNEQUIP, HEAL] or selected_inventory.items[item] == 1 else get_positive_num(f"\nHow m{'uch' if item in MATERIALS else 'any'} {item_display(item, 2)[2:]} do you want to {choice_name.lower().split('\n')[0]}{' with' if choice_name == HEAL else ''}?\n(there's {selected_inventory.items[item]}, leave blank to cancel)\n>>> ")
            if count < 0: continue

            rollback: bool = False
            display: str = item_display(item, count if choice_name == ADD_WITH_ITEMS or choice_name == DISCARD else (2 if item in ARMOR_REDUCTIONS and ARMOR_REDUCTIONS[item][1] else 0)).lower()
            try:
                if choice_name == ADD_WITH_ITEMS:
                    outside.remove(item, count)
                    rollback = True
                    player.inventory.add(item, count)
                    msg = f"Successfully added {display} to your inventory\n"
                elif choice_name == DISCARD:
                    outside.add(item, count)
                    rollback = True
                    player.inventory.remove(item, count)
                    msg = f"Successfully discarded {display} from your inventory\n"
                elif choice_name == EQUIP:
                    if equip_weapon: player.equip_weapon(item)
                    else: player.equip_armor(item)
                    msg = f"Successfully equipped {'another ' if equip_weapon and player.weapon[1] else ''}{display}\n"
                elif choice_name == UNEQUIP:
                    if equip_weapon: player.unequip_weapon()
                    else: player.unequip_armor(item)
                    msg = f"Successfully unequipped {'weapon' if equip_weapon else display}\n"
                else: msg = player.heal(item, in_battle)
            except (EquipmentError, InventoryError) as e:
                msg = f"{INVALID}{str(e)}\n"
                if rollback:
                    if choice_name == ADD_WITH_ITEMS: outside.add(item, count)
                    else: outside.remove(item, count)


# battle system
# -1 = lose
# 0 = fled
# 1 = won
def battle(player: Character, enemies: list[Character]) -> int:
    loot: Inventory = Inventory(capacity = -1)
    
    while len(enemies) > 0:
        player_defending: bool = False
        print(
"""
==========
  BATTLE
==========
You are in a fight with:
"""
        )
        for enemy in enemies: print(f"- {enemy_display(enemy, 2)}")

        print(
f"""
--------------
 QUICK STATUS
--------------
> {enemy_display(player, 2)}"""
        )

        # player does stuff
        choice: int = get_input(
            "\nSelect an option:\n",
            [
                "Attack",
                "Defend",
                "Management",
                "Flee"
            ]
        )
        attack_choice: int = 0

        if choice == 0:
            options: list[str] = []
            # + 3 because the formatting is
            # 0 - abcd
            #  ^^^
            indent: int = len(str(len(enemies) - 1)) + 3
            if len(enemies) > 1:
                for enemy in enemies: options.append(enemy_display(enemy, indent))
                attack_choice: int = get_input("\nSelect a target:\n", options)
        elif choice == 1: player_defending = True
        elif choice == 2:
            # you can loot in the middle of battle and this is intentional
            manage(player, loot, True)
            continue
        else: return 0

        sleep(1)
        chosen: Character = enemies[attack_choice]
        try: player.turn(None if player_defending else chosen)
        except EquipmentError as e:
            print(f"\nYou can't do that\n{str(e)}")
            continue
        if attack_choice != -1 and chosen.hp <= DEATH_THRESHOLD:
            sleep(1)
            print(f"\n{chosen.name} has been defeated!")
            chosen.inventory.capacity = -1
            chosen.unequip_weapon()
            chosen.unequip_weapon()
            for armor in ARMOR_REDUCTIONS: chosen.unequip_armor(armor)
            for item in chosen.inventory.items: loot.add(item, chosen.inventory.items[item])
            enemies.remove(chosen)
        sleep(1)

        # enemies attack
        for enemy in enemies:
            try: enemy.turn(player, player_defending)
            except InventoryError:
                enemy.unequip_weapon()
                enemy.unequip_weapon()
                enemy.turn(player, player_defending)
            if player.hp <= 0: return -1
            sleep(1)

    print("\nYou won the battle!\nManage the loot before continuing")
    sleep(2)
    manage(player, loot)
    return 1


# village mechanics
def village(player: Character) -> str:
    LEAVE: str = "Leave"
    CANCEL: str = "Cancel"

    player.hp = player.hp_cap
    print(f"\n{player.name} is now at full health.")
    while True:
        print(
"""
===========
  VILLAGE
===========
Do some trading with the villagers
"""
        )

        options: list[str] = [LEAVE]
        for section in SECTIONS: options.append(section.name)
        choice: int = get_input("Select a part of the village to visit:\n", options)
        if options[choice] == LEAVE: return ""

        section: VillageSection = SECTIONS[choice - 1]
        first: bool = True
        msg: str = ""
        while True:
            print(f"{section if first else section.show_trades()}\n{msg}")
            msg = ""
            first = False

            choice = get_input(
                "Select an option:\n",
                [
                    LEAVE,
                    "Management",
                    "Trade"
                ]
            )
            if choice == 0: break
            if choice == 1:
                manage(player)
                continue

            to_del_item_list: list[str] = []
            item_list: list[str] = list(player.inventory.items)
            for item in item_list:
                tradeable: bool = False
                for trade in section.trades:
                    if trade[0][1] == item or trade[1][1] == item:
                        tradeable = True
                        break
                if not(tradeable): to_del_item_list.append(item)
            for to_del in to_del_item_list: item_list.remove(to_del)

            if len(item_list) == 0:
                msg = "\nYou have nothing to offer for this villager\n"
                continue

            item_list.insert(0, CANCEL)
            offer_name: str = item_list[get_input("\nWhat do you want to offer? (or do you want to cancel?)\n", item_list)]
            if offer_name == CANCEL: continue
            offer_amt: int = get_positive_num(f"\nHow m{'uch' if offer_name in MATERIALS else 'any'} {item_display(offer_name, 2)[2:]} do you want to offer?\n(you have {player.inventory.items[offer_name]}, leave blank to cancel)\n>>> ") if player.inventory.items[offer_name] > 1 else 1
            if offer_amt < 0: continue
            offer: tuple[int, str] = (offer_amt, offer_name)


            possible_trades: list[tuple[tuple[int, str], tuple[int, str]]] = []
            for trade in section.trades:
                if trade[0][1] == offer[1] and trade[0][0] <= offer[0] or trade[1][1] == offer[1] and trade[1][0] <= offer[0]: possible_trades.append(trade)

            if len(possible_trades) == 0: msg = "\nNo trades match your offer\n"
            else:
                options = [CANCEL]
                for trade in possible_trades: options.append(show_trade(trade)[1:])
                choice = get_input("\nSelect a trade (or cancel):\n", options)
                if options[choice] == CANCEL: continue
                trade: tuple[tuple[int, str], tuple[int, str]] = possible_trades[choice - 1]

                rollback: bool = False
                flipped: bool = offer[1] == trade[1][1]
                this_side: tuple[int, str] = trade[1 if flipped else 0]
                other_side: tuple[int, str] = trade[0 if flipped else 1]
                mult: int = offer[0] // this_side[0]
                try:
                    player.inventory.remove(this_side[1], this_side[0] * mult)
                    rollback = True
                    player.inventory.add(other_side[1], other_side[0] * mult)
                    msg = section.thanks + f"(You gave {item_display(this_side[1], this_side[0] * mult).lower()} and now have {item_display(other_side[1], player.inventory.items[other_side[1]]).lower()})\n"
                except InventoryError as e:
                    if rollback: player.inventory.add(this_side[1], this_side[0] * mult)
                    msg = f"\nYou can't do that\n{str(e)}\n"


def enter_place(state: dict, player: Character, at: str) -> tuple[str, int]:
    same_spot: bool = state["search_x"] == state["px"] and state["search_y"] == state["py"]
    msg: str = ""
    result: int = 0

    if   at == VILLAGE: village(player)
    elif at == BANDITS:
        if same_spot: msg = "You already fought these bandits!\n"
        else:
            result = battle(player, [
                create_hard("Bandit", weapon = ("flintlock", False), inventory = Inventory(items = {"flintlock bullet": 6, "coin": 10})),
                create_hard("Bandit", weapon = ("sword", False), inventory = Inventory(items = {"bandage": 2, "healing potion": 1})),
            ])
            state["visited bandits"] = True
    elif at == DEFENSES:
        if same_spot: msg = "You already fought the castle's defenses!\n"
        elif state["actually finished"]: msg = "Do not fear, for your guards are free of the wizard's trance\n"
        else:
            result = battle(player, [
                create_beast("Dragon"),
                create_hard("Guard", weapon = ("musket", False), armor = {"helmet", "chestplate", "legging", "arm pad", "boot", "shield"}, inventory = Inventory(items = {"musket bullet": 15, "healing potion": 1})),
                create_hard("Guard", weapon = ("axe", True), armor = {"helmet", "chestplate", "legging", "arm pad", "boot"}, inventory = Inventory(items = {"healing potion": 2}))
            ])
    else:
        if state["actually finished"]: msg = f"You have already defeated the evil wizard!\n"
        else:
            sleep(1)
            print(
"""
You burst in, leaving the dragon and the guards at the door.
The sound of the doors slamming reverberates through the castle halls.

You start running.

You know this place already.

The red carpet is silky smooth.
The paintings on the walls are framed with gold.
Elegant chandeliers cover the ceiling, hanging on by a thread.

You take a left.
A right.
Another left.

You're still running down the halls.

...Then you see it.
Grand wooden double-doors.

You burst through, again, just like what you did to get in a few minutes ago.
The sunlight shines through the windows, more familliar than the back of your hand.
The door swings around and slams on the wall it's attached to,
the sound interrupting whatever moment you were having.

You hear a chuckle, then a taunting voice on the other side of the room.
"Well, well, well..."

"Shall we begin... our dance to the death?"
"""
            )
            sleep(1)
            input("Hit enter to continue\n")

            result = battle(player, [
                create_boss("Evil Wizard", weapon = ("magic staff", False), inventory = Inventory(items = {"coin": 100}))
            ])
            state["finished boss"] = result == 1

    if result == 1 or at != DEFENSES:
        state["search_x"] = state["px"]
        state["search_y"] = state["py"]

    state["dont visit"] = True
    state["player"] = player

    if result != -1: save(state, f"{player.name}{EXTENSION}", state["autosave"])
    return (msg, result)


def rand_encounter(state: dict) -> list[Character]:
    counter: int = 0
    enemy_list: list[Character] = []
    scale: float = min(ENCOUNTER_SCALING_LIMIT, (state["encounter"] - len(ENCOUNTERS)) * ENCOUNTER_SCALING)

    for i in range(randint(1, RAND_ENCOUNTER_MAX_ACTUAL)):
        enemy_type: int = randint(0, 3)
        # once the enemy count reaches RAND_ENCOUNTER_MAX_LOOSE,
        # swarm enemies can push the enemy count to RAND_ENCOUNTER_MAX_ACTUAL
        if enemy_type != 3 and counter >= RAND_ENCOUNTER_MAX_LOOSE: enemy_type = 3

        enemy_weapon: str = ""
        counter: int = 0
        for weapon in WEAPON_BONUSES:
            if random() < CHOOSE_WEAPON_CHANCE - scale or counter == CHOOSE_WEAPON_LIMIT:
                enemy_weapon = weapon
                break
            counter += 1

        enemy_armor: set = set()
        for armor in ARMOR_REDUCTIONS:
            if random() < APPLY_ARMOR_CHANCE + scale: enemy_armor.add(armor)

        DIFFICULTY_TABLE: dict[int, Callable[[str, tuple[str, bool], set[str], Inventory], Character]] = {
            0: create_easy,
            1: create_medium,
            2: create_hard,
            3: create_swarm
        }
        enemy_creation: Callable[[str, tuple[str, bool], set[str], Inventory], Character] = DIFFICULTY_TABLE[enemy_type]

        NAMES: list[list[str]] = [
            ["Goblin"],
            ["Orc"],
            ["Zombie", "Skeleton"],
            ["Imp"]
        ]

        enemy_list.append(enemy_creation(NAMES[enemy_type][randint(0, len(NAMES) - 1)], (enemy_weapon, random() < DUAL_WIELD_CHANCE), enemy_armor, drops(ENCOUNTER_DROPS)))
        if enemy_type != 3: counter += 1

    return enemy_list


# put it all together
# False = return to menu
# True = exit
def game(first: bool) -> bool:
    # main menu
    state: dict = {"retry": True}
    while "retry" in state:
        state = menu(first)
        first = False
        if state == {}: return True

    if state["first"]:
        sleep(1)
        
        print(
"""
A long, long time ago, there lived the ruler of a peaceful and prospering kingdom.
He walked with grace, yet he ruled with utmost discipline.

But then, something went wrong.

An old man in a robe walked up, every footstep thumping loud in the throne room.
In his hand lies a magic staff, glistening in the sunlight shining through the decorated windows.
"Who are you?", the ruler asked, half-curious and half-frustrated.

The man introduced himself, with an almost prophetic tone.
"Begone foul ruler, for I am a wizard, here to take thy throne!"

The ruler stood up, eyebrows furrowing, and said:
"Guards! Take this fool away!"
His tone was one which could pierce even the toughest of hearts.

But, the guards did not heed his call to action.
They just stood there, staring at nothing, in a trance.

The wizard walked closer, his smile widening, and said:
"Thou are finished! Thy castle and throne now belongs to me!"

With a swift and thundering movement of his magic staff,
the ruler was thrown up, and away from his throne by nothing but wind,
and began to feel the floor spin beneath him.

Spin, spin, and spin...
His arms flailed around, desperately trying to keep himself upright.
He had to close his eyes, for he saw flashes of light, everywhere and nowhere, all at the same time.

Then, just as suddenly as it started, it stops.

Everything becomes bright, blinding almost, and he falls over onto the grass.
"Grass...?" he utters to himself.

"The castle has ceramic tiling..."

To the north, he can see the lush green forest, which hides many dangers in the dark.
To the east, he can see the deep blue ocean, with the waves chipping at a lone village further north.

Further northeast, the ruler's grand castle sits in the safety of high walls,
each wall boasting a large dragon to fend off intruders.

As he pulls himself back together, cape firmly dirtied by the fall,
the severity of the situation finally begins to show.

He has been thrown from his castle, and must now stop the evil wizard,
before anything worse happens to his people.

(You might have to resize the window or scroll up for this one)
"""
        )

        sleep(1)
        input("Hit enter to continue\n")
        state["first"] = False

    # actual game
    msg: str = ""
    battle_result: int = -2
    while True:
        player: Character = state["player"]
        if battle_result == -1 or player.hp <= 0:
            state = lose(player.name)
            player = state["player"]
        elif battle_result >= 0 or state["autosave"]: save(state, f"{player.name}{EXTENSION}", state["autosave"])
        battle_result = -2

        map_with_player: str = "\n"
        x: int = state["px"]
        y: int = state["py"]
        for i in range(len(WORLD_MAP)): map_with_player += "@" if i == x + (x_bound() + 1) * y else WORLD_MAP[i]

        at: str = map_char_at(x, y)
        PLACES: list[str] = [CASTLE, BANDITS, VILLAGE, DEFENSES]
        at_place: bool = at in PLACES

        encounter_chance: float = 0
        if map_char_at(x, y) == PLAINS: encounter_chance = ENCOUNTER_CHANCE_LOW
        if map_char_at(x, y) == FOREST: encounter_chance = ENCOUNTER_CHANCE_HIGH
        trigger_encounter: bool = not(state["dont encounter"]) and random() < encounter_chance
        state["dont encounter"] = False

        if trigger_encounter:
            battle_result = battle(player, rand_encounter(state) if state["encounter"] >= len(ENCOUNTERS) else ENCOUNTERS[state["encounter"]])
            if battle_result == 1: state["encounter"] += 1
            state["dont encounter"] = True
            continue

        # auto-visit
        if at_place and not(state["dont visit"]) and msg == "":
            enter_result: tuple[str, int] = enter_place(state, player, at)
            msg = enter_result[0]
            battle_result = enter_result[1]
            if state["finished boss"]: break
            continue
        state["dont visit"] = False

        # do you like text art?
        print(
map_with_player + f"""
\nLegend:
 @ - You
 {CASTLE} - Your Castle
 {DEFENSES} - The Wall{f'\n {BANDITS} - Bandit Camp' if state['visited bandits'] else ''}
 {VILLAGE} - Village
 {OCEAN} - Ocean
 {PLAINS} - Plains
 {FOREST} - Dark Forest
\n{msg}Pick a direction, or select an action:

NW N NE
   |        0 - {'Enter place' if at_place else 'Search area'}
W--@--E     1 - Management
   |        2 - Options
SW S SE
"""
        )

        raw: str = input().lower().strip()
        msg = ""

        if raw.isdigit():
            choice: int = int(raw)
            if choice == 0:
                if at_place:
                    enter_result: tuple[str, int] = enter_place(state, player, at)
                    msg = enter_result[0]
                    battle_result = enter_result[1]
                    if state["finished boss"]: break
                elif not(state["search_x"] == x and state["search_y"] == y):
                    manage(player, drops(SEARCH_DROPS, -1))
                    state["search_x"] = x
                    state["search_y"] = y
                else: msg = "You can't search the same spot again\nGo somewhere else\n"
            elif choice == 1: manage(player)
            elif choice == 2:
                result: dict = options(state)
                if result == {}: return False
                if result != state: state = result
                state["dont encounter"] = True
            else: msg = "Invalid option\n"
            if choice != 0: state["dont visit"] = True
        # move
        elif raw != "":
            INVALID_DIR: str = "Invalid direction\n"
            movement_x: int = 0
            movement_y: int = 0
            
            if len(raw) == 0: msg = INVALID_DIR
            if len(raw) >= 1:
                move_n: bool = raw[0] == "n"
                move_s: bool = raw[0] == "s"
                move_w: bool = raw[0] == "w"
                move_e: bool = raw[0] == "e"
                if   move_n: movement_y -= 1
                elif move_s: movement_y += 1
                elif move_w: movement_x -= 1
                elif move_e: movement_x += 1
                else: msg = INVALID_DIR

                if len(raw) == 2:
                    if move_n or move_s:
                        if   raw[1] == "w": movement_x -= 1
                        elif raw[1] == "e": movement_x += 1
                        else: msg = INVALID_DIR
                    else: msg = INVALID_DIR
                elif len(raw) > 2: msg = INVALID_DIR

            # same condition 2x in a row, yuck
            if msg == "":
                destination: str = map_char_at(x + movement_x, y + movement_y)
                if destination == "" or destination == "\n": msg = INVALID_DIR
                elif destination == OCEAN: msg = INVALID_DIR + "That's the ocean!\n"
                elif destination == CASTLE and map_char_at(state["search_x"], state["search_y"]) != DEFENSES and not(state["actually finished"]): msg = INVALID_DIR + "You must get through the evil wizard's defenses first\n"

            # everything is clear, you can FINALLY move
            if msg == "":
                state["px"] += movement_x
                state["py"] += movement_y
        else: msg = "You have to type something...\n"

        # make sure we dont set this to False when it is already True
        if not(state["dont encounter"]):
            # make sure you dont get an encounter when you input something invalid or you're at a place
            state["dont encounter"] = msg != "" or map_char_at(state["px"], state["py"]) in PLACES

            # passive healing when moving
            if not(state["dont encounter"]): player.hp = min(player.hp_cap, player.hp + PASSIVE_HEAL)

    if not(state["actually finished"]):
        player: Character = state["player"]
        sleep(1)
        print(
f"""
The ruler struck the evil wizard with his {item_display(player.weapon[0], 2 if player.weapon[1] else 0)}.

He fell to the ground, his magic staff happening to roll over to the ruler's feet.

"You can have the staff, just... please, spare me!", the wizard cried, with desperation in every word.

The ruler thought for a moment, then took the wizard's magic staff.

"No...! Don't do it!"

With a swift and thundering movement of his magic staff, he casted the wizard to a land far, far away.


Thanks for playing my game!
 -- Carstyle476
"""
        )
        sleep(1)
        input("Hit enter to continue\n")

        state["actually finished"] = True
        state["finished boss"] = False
        successful: bool = save(state, f"{player.name}{EXTENSION}")
        if not(successful): print("\nWARNING: Could not save file for this special occasion!")

    return False


# wrap everything in a keyboardinterrupt try/except (yikes!!!)
def main() -> None:
    result: bool = False
    first: bool = True
    while not(result):
        try: result = game(first)
        except (KeyboardInterrupt, EOFError): return
        first = False

if __name__ == "__main__": main()
