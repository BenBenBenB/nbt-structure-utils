import copy
from collections.abc import Iterable

from nbt.nbt import TAG_Byte, TAG_Compound, TAG_Int, TAG_List, TAG_Short, TAG_String


class Enchantment:
    """Represents and gets NBT for an enchantment.

    Attributes:
        id (int): Enchantment name
        lvl (int): Enchantment level
    """

    id: str
    lvl: int

    def __init__(self, id: str, lvl: int) -> None:
        if ":" not in id:
            self.id = "minecraft:" + id
        else:
            self.id = id
        self.lvl = lvl

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id and self.lvl == __value.lvl

    def get_nbt(self) -> TAG_Compound:
        """Get the nbt representation of the enchantment."""
        nbt_enchant = TAG_Compound()
        nbt_enchant.tags.append(TAG_Short(name="lvl", value=self.lvl))
        nbt_enchant.tags.append(TAG_String(name="id", value=self.id))
        return nbt_enchant

    def copy(self) -> "Enchantment":
        """Create a copy of self."""
        return Enchantment(self.id, self.lvl)

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "Enchantment":
        """Create an equivalent Enchantment object from existing NBT."""
        return Enchantment(id=nbt["id"].value, lvl=nbt["lvl"].value)


class ItemStack:
    """Represents and gets NBT for a stack of items.

    Attributes:
        id : int
            Item name.
        count : int
            Number of Items.
        slot : int
            Position in inventory.
        damage : int
            Damage, if any.
        enchantments : list[Enchantment]
            enchantments on the item, if any
        other_tags: TAG_Compound
            any other NBT values on the item(s)
    """

    id: str
    count: int
    slot: int
    damage: int
    enchantments: "list[Enchantment]"
    other_tags: TAG_Compound

    def __init__(
        self,
        item_id: str,
        count: int,
        slot: int,
        damage: int = None,
        enchantments: "list[Enchantment]" = [],
        other_tags: TAG_Compound = None,
    ) -> None:
        if ":" not in item_id:
            self.id = "minecraft:" + item_id
        else:
            self.id = item_id
        self.count = count
        self.slot = slot
        self.damage = damage
        self.enchantments = enchantments if enchantments else []
        self.other_tags = copy.deepcopy(other_tags)

    def __eq__(self, __value: object) -> bool:
        if not (
            self.id == __value.id
            and self.count == __value.count
            and self.slot == __value.slot
            and self.damage == __value.damage
        ):
            return False
        if self.enchantments is None:
            return __value.enchantments is None
        else:
            return (
                __value.enchantments is not None
                and len(__value.enchantments) == len(self.enchantments)
                and all(e in __value.enchantments for e in self.enchantments)
            )

    def get_nbt(self) -> TAG_Compound:
        """Get the nbt representation of the item stack."""
        nbt_item = TAG_Compound()
        nbt_item.tags.append(TAG_Byte(name="Slot", value=self.slot))
        nbt_item.tags.append(TAG_String(name="id", value=self.id))
        nbt_item.tags.append(TAG_Byte(name="Count", value=self.count))
        if self.__needs_tags():
            nbt_item.tags.append(self.__get_tag_nbt())
        return nbt_item

    def __needs_tags(self) -> bool:
        return (
            (self.damage is not None)
            or (self.enchantments)
            or (self.other_tags and self.other_tags.tags)
        )

    def __get_tag_nbt(self) -> TAG_Compound:
        nbt_tag = TAG_Compound(name="tag")
        if self.damage is not None:
            nbt_tag.tags.append(TAG_Int(name="Damage", value=self.damage))
        if self.enchantments:
            nbt_enchantments = TAG_List(name="Enchantments", type=TAG_Compound)
            for enchant in self.enchantments:
                nbt_enchantments.tags.append(enchant.get_nbt())
            nbt_tag.tags.append(nbt_enchantments)
        if self.other_tags:
            nbt_tag.tags.extend(self.other_tags.tags)
        return nbt_tag

    def copy(self) -> "ItemStack":
        """Get a copy of the item stack."""
        return ItemStack(
            item_id=self.id,
            count=self.count,
            slot=self.slot,
            damage=self.damage,
            enchantments=[e.copy() for e in self.enchantments],
            other_tags=copy.deepcopy(self.other_tags),
        )

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "ItemStack":
        """Create an equivalent ItemStack object from existing NBT."""
        itemstack = ItemStack(
            item_id=nbt["id"].value,
            count=nbt["Count"].value,
            slot=nbt["Slot"].value,
        )
        if "tag" in nbt:
            tag_nbt = copy.deepcopy(nbt["tag"])
            if "Damage" in tag_nbt:
                itemstack.damage = tag_nbt["Damage"].value
                del tag_nbt["Damage"]
            if "Enchantments" in nbt["tag"]:
                itemstack.enchantments = [
                    Enchantment.load_from_nbt(e) for e in tag_nbt["Enchantments"].tags
                ]
                del tag_nbt["Enchantments"]
            if any(tag_nbt.tags):
                itemstack.other_tags = tag_nbt
        return itemstack


class Inventory:
    """Represents and gets NBT for all item stacks in an inventory.

    Attributes:
        items: list[ItemStack]
            All items in the inventory.
    """

    items: "list[ItemStack]"

    def __init__(self, items: "Iterable[ItemStack]" = []) -> None:
        self.items = [i.copy() for i in items]

    def get_nbt(self) -> TAG_Compound:
        """Get the nbt representation of the inventory."""
        nbt_inv_items = TAG_List(name="Items", type=TAG_Compound)
        for item in self.items:
            nbt_inv_items.tags.append(item.get_nbt())
        return nbt_inv_items

    def copy(self) -> "Inventory":
        """Get a copy of the inventory."""
        return Inventory([i.copy() for i in self.items])

    def __eq__(self, __value: object) -> bool:
        if len(self.items) != len(__value.items):
            return False
        return all(self.items.count(i) == __value.items.count(i) for i in self.items)

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "Inventory":
        """Create an equivalent Inventory object from existing NBT."""
        if "Items" not in nbt:
            return None
        return Inventory(
            items=[ItemStack.load_from_nbt(i) for i in nbt["Items"].tags],
        )
