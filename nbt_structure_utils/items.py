from nbt.nbt import (
    TAG_Byte,
    TAG_Compound,
    TAG_Int,
    TAG_List,
    TAG_Short,
    TAG_String,
)


class Enchantment:
    id: str
    lvl: int

    def __init__(self, id: str, lvl: int) -> None:
        self.id = id
        self.lvl = lvl

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id and self.lvl == __value.lvl

    def get_nbt(self) -> TAG_Compound:
        nbt_enchant = TAG_Compound()
        nbt_enchant.tags.append(TAG_Short(name="lvl", value=self.lvl))
        nbt_enchant.tags.append(TAG_String(name="id", value=self.id))
        return nbt_enchant

    def copy(self) -> "Enchantment":
        return Enchantment(self.id, self.lvl)

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "Enchantment":
        return Enchantment(id=nbt["id"].value, lvl=nbt["lvl"].value)


class ItemStack:
    id: str
    count: int
    slot: int
    damage: int
    enchantments: "list[Enchantment]"

    def __init__(
        self,
        item_id: str,
        count: int,
        slot: int,
        damage: int = None,
        enchantments: "list[Enchantment]" = [],
    ) -> None:
        self.id = item_id
        self.count = count
        self.slot = slot
        self.damage = damage
        self.enchantments = enchantments if enchantments else []

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
        nbt_item = TAG_Compound()
        nbt_item.tags.append(TAG_Byte(name="Slot", value=self.slot))
        nbt_item.tags.append(TAG_String(name="id", value=self.id))
        nbt_item.tags.append(TAG_Byte(name="Count", value=self.count))
        if self.__needs_tags():
            nbt_item.tags.append(self.__get_tag_nbt())
        return nbt_item

    def __needs_tags(self) -> bool:
        return (self.damage is not None) or (self.enchantments)

    def __get_tag_nbt(self) -> TAG_Compound:
        nbt_tag = TAG_Compound(name="tag")
        if self.damage is not None:
            nbt_tag.tags.append(TAG_Int(name="Damage", value=self.damage))
        if self.enchantments:
            nbt_enchantments = TAG_List(name="Enchantments", type=TAG_Compound)
            for enchant in self.enchantments:
                nbt_enchantments.tags.append(enchant.get_nbt())
            nbt_tag.tags.append(nbt_enchantments)
        return nbt_tag

    def copy(self) -> "ItemStack":
        return ItemStack(
            item_id=self.id,
            count=self.count,
            slot=self.slot,
            damage=self.damage,
            enchantments=[e.copy() for e in self.enchantments],
        )

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "ItemStack":
        itemstack = ItemStack(
            item_id=nbt["id"].value,
            count=nbt["Count"].value,
            slot=nbt["Slot"].value,
        )
        if "tag" in nbt:
            if "Damage" in nbt["tag"]:
                itemstack.damage = nbt["tag"]["Damage"].value
            if "Enchantments" in nbt["tag"]:
                itemstack.enchantments = [
                    Enchantment.load_from_nbt(e)
                    for e in nbt["tag"]["Enchantments"].tags
                ]
        return itemstack


class Inventory:
    items: "list[ItemStack]"

    def __init__(self, items: "list[ItemStack]" = []) -> None:
        self.items = items

    def get_nbt(self) -> TAG_Compound:
        nbt_inv_items = TAG_List(name="Items", type=TAG_Compound)
        for item in self.items:
            nbt_inv_items.tags.append(item.get_nbt())
        return nbt_inv_items

    def copy(self) -> "Inventory":
        return Inventory([i.copy() for i in self.items])

    def __eq__(self, __value: object) -> bool:
        if len(self.items) != len(__value.items):
            return False
        return all(self.items.count(i) == __value.items.count(i) for i in self.items)

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound) -> "Inventory":
        if "Items" not in nbt:
            return None
        return Inventory(
            items=[ItemStack.load_from_nbt(i) for i in nbt["Items"].tags],
        )
