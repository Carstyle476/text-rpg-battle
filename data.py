
from inventory import Inventory
from character import Character
from common import *


def show_trade(trade: tuple[tuple[int, str], tuple[int, str]]) -> str: return f"\n{item_display(trade[0][1], trade[0][0])} <-> {item_display(trade[1][1], trade[1][0])}"

class VillageSection:

    def __init__(self, name: str, greeting: str, thanks: str, trades: list[tuple[tuple[int, str], tuple[int, str]]]) -> None:
        self.name = name
        self.greeting = greeting
        self.thanks = thanks
        self.trades = trades

        for trade in self.trades:
            if trade[0][1] == trade[1][1]: raise ValueError(f"Invalid trade found: {show_trade(trade)}")

    def __repr__(self) -> str: return f"VillageSection('{self.name}', '{self.greeting}', '{self.thanks}', {self.trades})"

    def __str__(self) -> str: return self.greeting + self.show_trades()

    def show_trades(self) -> str:
        result = "\n(Trades go both ways)\n"
        for trade in self.trades: result += show_trade(trade)
        return result


SECTIONS: list[VillageSection] = [
    VillageSection(
        "Armorsmith",
        "\nHey there. What can I get for ya? I make the finest armor around here.",
        "\nHere ya go, thanks for stoppin' by!\n",
        [
            ((5, "coin"), (1, "shield")),
            ((4, "coin"), (1, "chestplate")),
            ((3, "coin"), (1, "helmet")),
            ((3, "coin"), (1, "legging")),
            ((2, "coin"), (1, "arm pad")),
            ((2, "coin"), (1, "boot")),
            ((1, "iron"), (1, "coin"))
        ]
    ),
    VillageSection(
        "Blacksmith",
        "\nHey, welcome to my blacksmithing workplace, shop, thing... Whatever, need anything?",
        "\nHere it is. Stay safe!\n",
        [
            ((5, "coin"), (1, "axe")),
            ((4, "coin"), (1, "sword")),
            ((4, "coin"), (1, "mace")),
            ((3, "coin"), (1, "dagger")),
            ((2, "coin"), (1, "knife")),
            ((1, "iron"), (1, "coin"))
        ]
    ),
    VillageSection(
        "Martial Arts Center",
        "\nGreetings. What can I help you with?",
        "\nIt is a pleasure to meet you.\n",
        [
            ((4, "coin"), (1, "staff")),
            ((3, "coin"), (1, "bow")),
            ((2, "coin"), (1, "nunchucks")),
            ((1, "coin"), (10, "arrow")),
            ((1, "coin"), (2, "boomerang")),
            ((1, "iron"), (5, "shuriken")),
            ((2, "wood"), (1, "coin"))
        ]
    ),
    VillageSection(
        "Hospital",
        "\nHello dear. Please, take a seat.",
        "\nTake this.\n",
        [
            ((3, "coin"), (1, "healing potion")),
            ((2, "coin"), (1, "pill")),
            ((1, "coin"), (1, "bandage")),
            ((1, "glass bottle"), (2, "coin")),
            ((2, "used bandage"), (1, "coin"))
        ]
    ),
    VillageSection(
        "Gunsmith",
        "\nHey. How ya been? Straight to the point, shall we?",
        "\nHere.\n",
        [
            ((9, "coin"), (1, "musket")),
            ((7, "coin"), (1, "flintlock")),
            ((5, "coin"), (10, "musket bullet")),
            ((3, "coin"), (10, "flintlock bullet")),
            ((1, "iron"), (1, "coin"))
        ]
    )
]


# name, max, chance of 1 to drop
ENCOUNTER_DROPS: list[tuple[str, int, float]] = [
    ("stick",            3, 0.2),
    ("stone",            3, 0.2),
    ("wood",             3, 0.2),
    
    ("iron",             2, 0.15),
    
    ("arrow",            3, 0.1),
    ("bandage",          1, 0.1),
    ("used bandage",     1, 0.1),
    ("boomerang",        1, 0.1),
    
    ("glass bottle",     1, 0.05),
    ("healing potion",   1, 0.05),
    ("coin",             3, 0.05),
    ("shuriken",         3, 0.05),
    ("bow",              1, 0.05),
    ("boot",             1, 0.05),
    ("arm pad",          1, 0.05),
    ("legging",          1, 0.05),
    ("flintlock bullet", 3, 0.05),
    ("musket bullet",    3, 0.05),
]

SEARCH_DROPS: list[tuple[str, int, float]] = [
    ("stick",            5, 0.2),
    ("stone",            5, 0.2),
    ("wood",             5, 0.2),
    
    ("iron",             4, 0.15),
    
    ("arrow",            5, 0.1),
    ("flintlock bullet", 5, 0.1),
    ("musket bullet",    5, 0.1),
    
    ("boomerang",        1, 0.05),
    ("slingshot",        2, 0.05),
    ("knife",            1, 0.05),
    ("bandage",          2, 0.05),
    ("used bandage",     2, 0.05),
    
    ("nunchucks",        1, 0.02),
    ("coin",             5, 0.02),
    ("slingshot",        1, 0.02),
    ("knife",            1, 0.02),
    ("axe",              1, 0.02),
    ("mace",             1, 0.02),
    ("sword",            1, 0.02),
    ("axe",              1, 0.02),
    ("shuriken",         5, 0.02),
    ("bow",              1, 0.02),
    ("boot",             1, 0.02),
    ("arm pad",          1, 0.02),
    ("legging",          1, 0.02),
    ("helmet",           1, 0.02),
    ("glass bottle",     2, 0.02),
    ("healing potion",   2, 0.02),
    ("chestplate",       1, 0.02),
    ("shield",           1, 0.02)
]


CASTLE: str = "!"
BANDITS: str = "B"
VILLAGE: str = "V"
DEFENSES: str = "#"
FOREST: str = ";"
PLAINS: str = "."
OCEAN: str = "~"


WORLD_MAP: str = f"""{FOREST * 6}{PLAINS * 7}{DEFENSES}{CASTLE}
{FOREST * 7}{PLAINS * 6}{DEFENSES * 2}
{FOREST * 4}{BANDITS}{FOREST * 2}{PLAINS * 8}
{FOREST * 5}{PLAINS * 8}{OCEAN * 2}
{FOREST * 3}{PLAINS * 7}{VILLAGE}{PLAINS}{OCEAN * 3}
{FOREST}{PLAINS * 10}{OCEAN * 4}
{PLAINS * 11}{OCEAN * 4}
{PLAINS * 10}{OCEAN * 5}
{PLAINS * 10}{OCEAN * 5}
{PLAINS * 10}{OCEAN * 5}"""

def x_bound() -> int: return len(WORLD_MAP.split("\n")[0])

def map_char_at(x: int, y: int) -> str:
    idx: int = x + (x_bound() + 1) * y
    return "" if not(idx in range(len(WORLD_MAP))) else WORLD_MAP[idx]


# weapon, armor and inventory doubles as loot

def create_easy(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 30, 30, 5, 0, weapon, armor, inventory)
def create_medium(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 60, 60, 10, 0, weapon, armor, inventory)
def create_hard(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 90, 90, 10, 0, weapon, armor, inventory)
def create_swarm(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 10, 10, 3, 0, weapon, armor, inventory)
def create_beast(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 250, 250, 50, 0, weapon, armor, inventory)
def create_boss(name: str, weapon: tuple[str, bool] | None = None, armor: set[str] | None = None, inventory: Inventory | None = None) -> Character: return Character(name, 500, 500, 25, 0, weapon, armor, inventory)


ENCOUNTERS: dict[int, list[Character]] = {
    0:
    [
        create_easy("Goblin", inventory = Inventory(items = {"boomerang": 1}))
    ],
    
    1:
    [
        create_easy("Goblin", weapon = ("stick", False), inventory = Inventory(items = {"wood": 1, "stick": 1}))
    ],
    
    2:
    [
        create_easy("Goblin", weapon = ("knife", False), inventory = Inventory(items = {"slingshot": 1, "bandage": 1}))
    ],
    
    3:
    [
        create_medium("Orc", inventory = Inventory(items = {"dagger": 1}))
    ],
    
    4:
    [
        create_swarm("Imp", inventory = Inventory(items = {"iron": 1, "bandage": 2})),
        create_swarm("Imp", inventory = Inventory(items = {"glass bottle": 1}))
    ],

    5:
    [
        create_easy("Goblin", weapon = ("knife", False), armor = {"arm pad"}, inventory = Inventory(items = {"bandage": 1})),
        create_swarm("Imp", weapon = ("stone", True), inventory = Inventory(items = {"healing potion": 1, "stone": 2}))
    ],

    6:
    [
        create_hard("Thief", weapon = ("dagger", False), armor = {"chestplate"}, inventory = Inventory(items = {"bandage": 3}))
    ],

    7:
    [
        create_medium("Orc", weapon = ("knife", True), armor = {"arm pad", "legging"}),
        create_medium("Orc", weapon = ("knife", False), armor = {"helmet"}, inventory = Inventory(items = {"shuriken": 2}))
    ],

    8:
    [
        create_hard("Archer", weapon = ("bow", False), armor = {"chestplate"}, inventory = Inventory(items = {"arrow": 15}))
    ],

    9:
    [
        create_easy("Goblin", weapon = ("dagger", False), inventory = Inventory(items = {"glass bottle": 1})),
        create_easy("Goblin", weapon = ("knife", True), inventory = Inventory(items = {"bandage": 2})),
        create_easy("Goblin", weapon = ("sword", False), inventory = Inventory(items = {"wood": 3}))
    ],

    10:
    [
        create_medium("Orc", weapon = ("mace", False), armor = {"chestplate"}, inventory = Inventory(items = {"iron": 2})),
        create_easy("Goblin", weapon = ("dagger", False), inventory = Inventory(items = {"healing potion": 1})),
        create_easy("Goblin", weapon = ("dagger", False), inventory = Inventory(items = {"flintlock bullet": 1}))
    ],

    11:
    [
        create_hard("Zombie", inventory = Inventory(items = {"used bandage": 1})),
        create_hard("Zombie")
    ],

    12:
    [
        create_swarm("Imp", weapon = ("dagger", False)),
        create_swarm("Imp", weapon = ("dagger", False)),
        create_swarm("Imp", weapon = ("dagger", False)),
        create_swarm("Imp", weapon = ("dagger", False))
    ]
}
