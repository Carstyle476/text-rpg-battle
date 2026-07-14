
class InventoryError(Exception): pass
class EquipmentError(Exception): pass

MATERIALS: list[str] = [
    "wood",
    "iron"
]

VALUE_ROUND: int = 2

def item_display(item: str, count: int = 0, suffix: bool = False) -> str:
    if item == "": return ""
    plural: bool = count > 1
    is_material: bool = item in MATERIALS
    ends_with_s: bool = item[-1] == "s"
    set_of: str = f"set{'s' if plural else ''} of " if ends_with_s else ""
    prefix: str = f"{count} " if plural or is_material else (f"A{'n' if not(ends_with_s or plural) and item[0] in 'aeiou' else ''} " if count == 1 else "")
    desc_suffix: str = f" {'are' if (plural or ends_with_s) and not(is_material) else 'is'}" if suffix else ""
    return prefix + set_of + f"{item}{'s' if plural and not(ends_with_s or is_material) else ''}" + desc_suffix
