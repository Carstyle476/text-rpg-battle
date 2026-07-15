
from common import *
from character import Character, WEAPON_BONUSES, ARMOR_REDUCTIONS, HEALING_ITEMS
from inventory import Inventory
from data import *
from json import dumps, loads, JSONDecodeError

from random import random, randint
from time import sleep


EXTENSION: str = ".save"
PASSIVE_HEAL: int = 5

RAND_ENCOUNTER_MAX_LOOSE: int = 3 # i call this a "loose requirement", swarm enemies can push over this limit
RAND_ENCOUNTER_MAX_ACTUAL: int = 5 # the ACTUAL requirement

CHOOSE_WEAPON_CHANCE: float = 0.15 # per weapon, move to next if it lands "false"
CHOOSE_WEAPON_LIMIT: int = 14 # how far down the list it can go
DUAL_WIELD_CHANCE: float = 0.15

APPLY_ARMOR_CHANCE: float = 0.1 # per armor piece

ENCOUNTER_CHANCE_LOW: float = 0.1
ENCOUNTER_CHANCE_HIGH: float = 0.2

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


# save/load game state
# true = all good
# false = not good
def save(state: dict, file: str, dont_ask: bool = False) -> bool:
    saveable: dict = dict(state)
    if "player" in saveable: saveable["player"] = Character.save(saveable["player"])
    try:
        with open(file, mode = "x") as save_file: save_file.write(dumps(saveable))
    except FileExistsError:
        if dont_ask or input("\nSave file already exists\nDo you want to overwrite it? (y/n)\n>>> ").lower().strip() == "y":
            with open(file, mode = "w") as save_file: save_file.write(dumps(saveable))
            return True
        return False
    except OSError as e:
        print("\nCould not save file\n{repr(e)}")
        return False
    return True

def load(file: str) -> dict:
    with open(file, mode = "r") as save_file:
        loaded: dict = loads(save_file.read())
        if "player" in loaded: loaded["player"] = Character.load(loaded["player"])
        if "dont encounter" in loaded: loaded["dont encounter"] = True
        return loaded

# keep asking user for save name if invalid
def load_safely() -> dict[str, bool | int | Character]:
    while True:
        given_name: str = input("\nEnter save name (leave blank to cancel)\n>>> ")
        if given_name == "": return {"retry": True}
        try: return load(f"{given_name}{EXTENSION}")
        except JSONDecodeError: print("\nSave file is corrupted, please make a new save")
        except (OSError, FileNotFoundError): print("\nFile not found, please try again")


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


# if this returns negative then cancel whatever it's for
def get_positive_num(ask: str) -> int:
    while True:
        raw: str = input(ask).strip()
        if raw == "": return -1
        if raw.isdigit(): return int(raw)
        print("\nInvalid input, try again...")


def enemy_display(enemy: Character, indent: int) -> str:
    indent_str: str = " " * indent
    result: str = f"""{enemy.name}  ({enemy.hp}/{enemy.hp_cap} HP)
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
    print("\nYou died...\nReloading save")
    sleep(1)
    loaded: dict = load(f"{name}{EXTENSION}")
    if "dont encounter" in loaded: loaded["dont encounter"] = True
    return loaded


# main menu
# returns game state
def menu(welcome: bool = True) -> dict:
    print(f"\nMAIN MENU{'\nWelcome to the game!\n(Please, do not make typos)' if welcome else ''}")
    
    choice: int = get_input(
        "Select an option:\n",
        [
            "Exit",
            "New game",
            "Load game"
        ]
    )

    if choice == 1:
        name: str = ""
        while name == "":
            name = input("\nWhat's your name, traveller?\n(leave blank to cancel)\n>>> ").strip()
            if name == "": return {"retry": True}
        
        new_game: dict[str, bool | int | Character] = {
            "player": Character(name, 100, 100, 10),
            "px": 0,
            "py": len(WORLD_MAP.split("\n")) - 1,
            "search_x": -1,
            "search_y": -1,
            "encounter": 0,
            "autosave": input("\nDo you want to enable autosave?\nEvery action will be saved automatically without asking (y/n)\n>>> ").lower().strip() == "y",
            "dont encounter": True,
            "visited bandits": False,
            "first": True,
            "finished boss": False,
            "actually finished": False
        }

        successful: bool = save(new_game, f"{name}{EXTENSION}", False)
        if not(successful): return {"retry": True}
        return new_game
    if choice == 2: return load_safely()
    return {}


# options menu
# blank dict - quit to menu
# same dict - back to game
# different dict - load that
def options(state: dict) -> dict:
    choice: int = -1
    while choice != 4:
        print("\nOPTIONS")
        
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
            attempt: dict = load_safely()
            if not("retry" in attempt): return attempt
        if choice == 3:
            state["autosave"] = not(state["autosave"])
            save(state, f"{state['player'].name}{EXTENSION}", state["autosave"])

    state["dont encounter"] = True
    return state


# inventory management menu
def manage(player: Character, outside: Inventory | None = None, in_battle: bool = False) -> None:
    ADD: str = "Add"
    DISCARD: str = "Discard"
    EQUIP: str = "Equip"
    UNEQUIP: str = "Unequip"
    HEAL: str = "Heal"
    DONE: str = "Back"
    INVALID: str = "You can't do that\n"
    
    if outside is None: outside = Inventory(capacity = -1)
    
    choice: int = -1
    msg: str = ""
    while True:
        print(f"\nINVENTORY MANAGEMENT")
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

        print(player)

        print(msg)
        msg = ""
        choice_name: str = options[get_input("Select an option:\n", options)]
        if choice_name == DONE: return
        else:
            count: int = 0
            equip_weapon: bool = False

            outside_options: list[str] = list(outside.items)
            inside_options: list[str] = list(player.inventory.items)
            for armor in player.armor_set: inside_options.append(armor)
            if player.weapon[0] != "": inside_options.append(player.weapon[0])

            if choice_name == EQUIP or choice_name == UNEQUIP:
                skip: bool = False
                while True:
                    un: str = "E" if choice_name == EQUIP else "Une"
                    raw: str = input(f"\nSelect an option (leave blank to cancel):\n\n0 - {un}quip a weapon\n1 - {un}quip an armor piece\n\n").strip()
                    if raw == "":
                        skip = True
                        break
                    if raw == "0" or raw == "1":
                        equip_weapon = raw == "0"
                        break
                    print("\nInvalid input, try again\n")
                if skip: continue

            # delete options accordingly
            in_op_deletes: list[str] = []
            for item in inside_options:
                is_equippable: bool = equip_weapon and item in WEAPON_BONUSES or not(equip_weapon) and item in ARMOR_REDUCTIONS
                delete_equip: bool = choice_name == EQUIP and not(is_equippable)
                delete_unequip: bool = choice_name == UNEQUIP and (item in player.inventory.items or is_equippable)
                delete_heal: bool = choice_name == HEAL and not(item in HEALING_ITEMS)
                if delete_equip or delete_unequip or delete_heal: in_op_deletes.append(item)

            for to_delete in in_op_deletes: inside_options.remove(to_delete)

            correct_options: list[str] = outside_options if choice_name == ADD_WITH_ITEMS else inside_options
            if len(correct_options) == 0:
                msg = INVALID
                continue
            item: str = correct_options[0 if len(correct_options) == 1 else get_input("\nSelect an option:\n", correct_options)]
            # VERY dodgy one-liner
            if choice_name != UNEQUIP: count: int = 1 if (outside if choice_name == ADD_WITH_ITEMS else player.inventory).items[item] == 1 else get_positive_num(f"\nHow m{'uch' if item in MATERIALS else 'any'} {item_display(item, 2)[2:]} do you want to {choice_name.lower().split("\n")[0]}{' with' if choice_name == HEAL else ''}?\n>>> ")
            if count < 0: continue

            rollback: bool = False
            try:
                if choice_name == ADD_WITH_ITEMS:
                    outside.remove(item, count)
                    rollback = True
                    player.inventory.add(item, count)
                    msg = "Successfully added item to your inventory\n"
                elif choice_name == DISCARD:
                    outside.add(item, count)
                    rollback = True
                    player.inventory.remove(item, count)
                    msg = "Successfully discarded item from your inventory\n"
                elif choice_name == EQUIP:
                    if equip_weapon: player.equip_weapon(item)
                    else: player.equip_armor(item)
                    msg = f"Successfully equipped {'weapon' if equip_weapon else 'armor piece'}\n"
                elif choice_name == UNEQUIP:
                    if equip_weapon: player.unequip_weapon()
                    else: player.unequip_armor(item)
                    msg = f"Successfully unequipped {'weapon' if equip_weapon else 'armor piece'}\n"
                else:
                    player.heal(item, in_battle)
                    msg = f"Successfully healed up"
            except (EquipmentError, InventoryError):
                msg = INVALID
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
        print("\nBATTLE\nYou are under attack from:\n")
        for enemy in enemies: print(f"- {enemy_display(enemy, 2)}")
        
        # player does stuff
        choice: int = get_input(
            "\nSelect an option:\n",
            [
                "Attack",
                "Defend",
                "Manage",
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
        player.turn(None if player_defending else chosen)
        if attack_choice != -1 and chosen.hp <= DEATH_THRESHOLD:
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
                enemy.turn(player, player_defending)
            if player.hp <= 0: return -1
            sleep(1)

    print("\nYou won the battle!\nManage the loot before continuing")
    sleep(2)
    manage(player, loot)
    return 1


# village mechanics
def village(player: Character) -> None:
    LEAVE: str = "Leave"

    while True:
        options: list[str] = []
        options.append(LEAVE)
        for section in SECTIONS: options.append(section.name)

        choice: int = get_input("\nSelect a part of the village to visit:\n", options)
        if options[choice] == LEAVE: return

        section: VillageSection = SECTIONS[choice]
        first: bool = True
        msg: str = ""
        while True:
            print(section if first else section.show_trades())
            print(msg)
            msg = ""
            first = False

            choice = get_input(
                "Select an option:\n",
                [
                    LEAVE,
                    "Manage",
                    "Trade"
                ]
            )
            if choice == 0: break
            if choice == 1:
                manage(player)
                continue

            item_list: list[str] = list(player.inventory.items)
            CANCEL: str = "Cancel"
            item_list.insert(0, CANCEL)
            offer_name: str = item_list[get_input("\nWhat do you want to offer? (or do you want to cancel?)\n", item_list)]
            if offer_name == CANCEL: continue
            offer_amt: int = get_positive_num(f"\nHow m{'uch' if offer_name in MATERIALS else 'any'} {item_display(offer_name, 2)[2:]} do you want to offer?\n(leave blank to cancel)\n>>> ") if offer_name in player.inventory.items and player.inventory.items[offer_name] > 1 else 1
            if offer_amt < 0: continue
            offer: tuple[int, str] = (offer_amt, offer_name)


            possible_trades: list[tuple[tuple[int, str], tuple[int, str]]] = []
            for trade in section.trades:
                if trade[0][1] == offer[1] and offer[0] % trade[0][0] == 0 and trade[0][0] <= offer[0] or trade[1][1] == offer[1] and offer[0] % trade[1][0] == 0 and trade[1][0] <= offer[0]: possible_trades.append(trade)

            def attempt_trade(trade: tuple[tuple[int, str], tuple[int, str]]) -> str:
                rollback: bool = False
                flipped: bool = offer == trade[1]
                other_side: tuple[int, str] = trade[0] if flipped else trade[1]
                try:
                    player.inventory.remove(offer[1], offer[0])
                    rollback = True
                    player.inventory.add(other_side[1], other_side[0] * (offer[0] // (trade[1 if flipped else 0][0])))
                    return section.thanks
                except InventoryError as e:
                    if rollback: player.inventory.add(offer[1], offer[0])
                    return "\nYou can't do that\n"

            if len(possible_trades) == 0: msg = "\nNo trades match your offer\n"
            else:
                options = []
                for trade in possible_trades: options.append(show_trade(trade)[1:])
                choice = 0 if len(options) == 1 else get_input("\nSelect a trade:\n", options)
                msg = attempt_trade(possible_trades[choice])

        # heal up the player
        player.hp = player.hp_cap


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

A wizard walked up, fabulous yet crude, and said to the ruler:
"Begone thou, as I shall now take thy throne, which rightfully belongs to me!"

The ruler stood up, eyebrows furrowing, and said:
"Guards! Take this fool away!"
His tone was one which could pierce even the toughest of hearts.

But, the guards did not heed his call to action.
They just stood there, staring at nothing, in a trance.

The wizard walked closer, his smile widening, and said:
"Thou are finished! Thy castle and throne now belongs to me!"

With a swift and thundering movement of his magic staff,
the ruler was thrown up, and away from his throne by nothing but wind,
and started to feel the floor spin beneath him.

Spin, spin, and spin...
His arms flailed around, desperately trying to keep himself upright.
He had to close his eyes, for he saw flashes of light, everywhere and nowhere, all at the same time.

Then, just as suddenly as it started, it stops.

Everything becomes bright, blinding almost, and he falls over onto the grass.
"Grass...?" he utters to himself.

"The castle has ceramic tiling..."

To the north, he can see the lush green forest.
To the east, he can see the deep blue ocean.

As he pulls himself back together, cape firmly dirtied by the fall,
the severity of the situation finally begins to show.

He has been thrown from his castle, and must now stop the evil wizard,
before anything worse happens to his people.

"""
        )

        sleep(1)
        input("Hit enter to continue\n")
        state["first"] = False

    # actual game
    msg: str = ""
    battle_result: int = -2
    while not(state["finished boss"]):

        player: Character = state["player"]
        map_with_player: str = "\n"
        x: int = state["px"]
        y: int = state["py"]
        for i in range(len(WORLD_MAP)): map_with_player += "@" if i == x + (x_bound() + 1) * y else WORLD_MAP[i]

        at: str = map_char_at(x, y)
        at_place: bool = at in [CASTLE, BANDITS, VILLAGE, DEFENSES]

        encounter_chance: float = 0
        if map_char_at(x, y) == PLAINS: encounter_chance = ENCOUNTER_CHANCE_LOW
        if map_char_at(x, y) == FOREST: encounter_chance = ENCOUNTER_CHANCE_HIGH
        trigger_encounter: bool = random() < encounter_chance and not(state["dont encounter"])
        state["dont encounter"] = False

        if trigger_encounter:
            # follow the list of scripted encounters
            # when it runs out, start making stuff up
            enemy_list: list[Character] = []
            if state["encounter"] >= len(ENCOUNTERS):
                counter: int = 0
                scale: float = min(ENCOUNTER_SCALING_LIMIT, (state["encounter"] - len(ENCOUNTERS)) * ENCOUNTER_SCALING)
                for i in range(randint(1, RAND_ENCOUNTER_MAX_ACTUAL)):
                    enemy_type: int = randint(0, 3)

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

                    # this is some VERY VERY questionable code...
                    enemy_creation: object = create_easy
                    if enemy_type == 1: enemy_creation = create_medium
                    if enemy_type == 2: enemy_creation = create_hard
                    if enemy_type == 3 or counter >= RAND_ENCOUNTER_MAX_LOOSE: enemy_creation = create_swarm

                    names: list[str] = ["Goblin"]
                    if enemy_type == 1: names[0] = "Orc"
                    if enemy_type == 2: names = ["Zombie", "Skeleton"] 
                    if enemy_type == 3: names[0] = "Imp"

                    enemy_list.append(enemy_creation(names[randint(0, len(names) - 1)], (enemy_weapon, random() < DUAL_WIELD_CHANCE), enemy_armor, drops(ENCOUNTER_DROPS)))
                    if enemy_type != 3: counter += 1
            else: enemy_list = ENCOUNTERS[state["encounter"]]
            
            battle_result = battle(player, enemy_list)
            if battle_result == 1: state["encounter"] += 1
            state["dont encounter"] = True
            continue

        print(
map_with_player + (f"""
\nLegend:
 @ - You
 {CASTLE} - The Castle
 {DEFENSES} - The Wall{f'\n {BANDITS} - The Bandit Camp' if state['visited bandits'] else ''}
 {VILLAGE} - The Village
 {OCEAN} - Ocean
 {PLAINS} - The Plains
 {FOREST} - Dark Forest
\n{msg}Pick a direction, or select an action:

NW N NE
   |        0 - {'Enter' if at_place else 'Search'}
W--@--E     1 - Management
   |        2 - Options
SW S SE
""" if not(trigger_encounter) else "")
        )

        raw: str = input().lower().strip()

        msg = ""
        if raw.isdigit():
            choice: int = int(raw)
            if choice == 0:
                if state["search_x"] == x and state["search_y"] == y: msg = "You can't search the same spot again\nGo somewhere else\n"
                else:
                    if at_place:
                        if   at == VILLAGE: village(player)
                        elif at == BANDITS:
                            battle_result = battle(player, [
                                create_hard("Bandit", weapon = ("flintlock", False), inventory = Inventory(items = {"flintlock bullet": 6, "coin": 10})),
                                create_hard("Bandit", weapon = ("sword", False), inventory = Inventory(items = {"bandage": 3, "healing potion": 1})),
                            ])
                            state["visited bandits"] = True
                        elif at == DEFENSES:
                            if state["actually finished"]: msg = "Do not fear, for your guards are free of the wizard's trance\n"
                            else:
                                battle_result = battle(player, [
                                    create_beast("Dragon"),
                                    create_hard("Guard", weapon = ("musket", False), armor = {"helmet", "chestplate", "legging", "arm pad", "boot", "shield"}, inventory = Inventory(items = {"musket bullet": 15, "healing potion": 1})),
                                    create_hard("Guard", weapon = ("axe", True), armor = {"helmet", "chestplate", "legging", "arm pad", "boot", "shield"}, inventory = Inventory(items = {"healing potion": 3}))
                                ])
                        else:
                            if state["actually finished"]: msg = f"You have already defeated the evil wizard!\n"
                            else:
                                battle_result = battle(player, [
                                    create_boss("Evil Wizard", weapon = ("magic staff", False), inventory = Inventory(items = {"coin": 100, "ring": 1}))
                                ])
                                state["finished boss"] = battle_result == 1
                    else: manage(player, drops(SEARCH_DROPS, -1))

                    if at_place and battle_result == 1 or not(at_place):
                        state["search_x"] = x
                        state["search_y"] = y
                        if at_place: state["dont encounter"] = True
            elif choice == 1: manage(player)
            elif choice == 2:
                result: dict = options(state)
                if result == {}: return False
                if result != state: state = result
                state["dont encounter"] = True
            else: msg = "Invalid option\n"
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

            destination: str = map_char_at(x + movement_x, y + movement_y)
            if destination == "" or destination == "\n": msg = INVALID_DIR
            elif destination == OCEAN: msg = INVALID_DIR + "That's the ocean!\n"
            elif destination == CASTLE and map_char_at(state["search_x"], state["search_y"]) != DEFENSES and not(state["finished boss"]): msg = INVALID_DIR + "You must get through the evil wizard's defenses first\n"

            if msg == "":
                state["px"] += movement_x
                state["py"] += movement_y

        if not(state["dont encounter"]): state["dont encounter"] = msg != "" or raw == "" or at_place
        if not(state["dont encounter"]) or at_place: player.hp = min(player.hp_cap, player.hp + PASSIVE_HEAL)

        if battle_result == -1: state = lose(player.name)
        elif battle_result >= 0 or state["autosave"]: save(state, f"{player.name}{EXTENSION}", state["autosave"])
        battle_result = -2

    if state["finished boss"] and not(state["actually finished"]):
        if save(state, f"{player.name}{EXTENSION}", state["autosave"]):
            player: Character = state["player"]
            sleep(1)
            print(
f"""

The ruler struck down on the evil wizard with his {item_display(player.weapon[0], 2 if player.weapon[1] else 0)}.

"Please, spare me!", the wizard cried.

The ruler thought for a moment, then took the wizard's magic staff.

"No...! Don't do it!"

With a swift and thundering movement of his magic staff, he casted the wizard to a land far, far away.


Thank you for playing my game!
 -- Carstyle476

"""
            )
            sleep(1)
            input("Hit enter to continue\n")
            state["actually finished"] = True
            state["finished boss"] = True

    return False


# wrap everything in a keyboardinterrupt try/except (yikes!!!)
def main() -> None:
    result: bool = False
    first: bool = True
    while not(result):
        try: result = game(first)
        except KeyboardInterrupt: return
        first = False

if __name__ == "__main__": main()
