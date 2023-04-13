from nbt.nbt import TAG_Compound, TAG_String


class BlockData:
    name: str
    properties: list[tuple]

    def __init__(self, item_id: str, props: list[tuple] = []) -> None:
        if ":" not in item_id:
            self.name = "minecraft:" + item_id
        else:
            self.name = item_id
        self.properties = props.copy()

    def __eq__(self, __o: object) -> bool:
        if __o is None:
            return False
        return self.name == __o.name and sorted(self.properties) == sorted(
            __o.properties
        )

    def copy(self) -> "BlockData":
        return BlockData(self.name, self.properties)

    def get_nbt(self) -> TAG_Compound:
        nbt_block_state = TAG_Compound()
        if any(self.properties):
            block_properties = TAG_Compound(name="Properties")
            for prop in self.properties:
                block_properties.tags.append(
                    TAG_String(name=prop[0], value=str(prop[1]))
                )
            nbt_block_state.tags.append(block_properties)
        nbt_block_state.tags.append(TAG_String(name="Name", value=self.name))
        return nbt_block_state

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound()) -> "BlockData":
        name = nbt["Name"].value
        properties = []
        if "Properties" in nbt:
            properties = [(p.name, p.value) for p in nbt["Properties"].tags]
        return BlockData(name, properties)


def bool_to_str(value: bool) -> str:
    return "true" if value else "false"


def get_trap_door(material: str, facing: str, half: str) -> BlockData:
    name = "minecraft:" + material + "_trapdoor"
    return BlockData(name, [("facing", facing), ("half", half)])


def get_button(material: str, facing: str, face: str) -> BlockData:
    name = "minecraft:" + material + "_button"
    return BlockData(name, [("facing", facing), ("face", face)])


def get_dropper(facing: str) -> BlockData:
    return BlockData("minecraft:dropper", [("facing", facing)])


def get_piston(facing: str) -> BlockData:
    return BlockData("minecraft:piston", [("facing", facing)])


def get_sticky_piston(facing: str) -> BlockData:
    return BlockData("minecraft:sticky_piston", [("facing", facing)])


def get_observer(facing: str) -> BlockData:
    return BlockData("minecraft:observer", [("facing", facing)])


def get_repeater(facing: str, delay: int) -> BlockData:
    return BlockData("minecraft:repeater", [("facing", facing), ("delay", str(delay))])


def get_comparator(facing: str, mode: str) -> BlockData:
    return BlockData("minecraft:comparator", [("facing", facing), ("mode", mode)])


def get_redstone_torch(lit: bool = True, facing: str = None) -> BlockData:
    if facing is None:
        return BlockData("minecraft:redstone_torch", [("lit", bool_to_str(lit))])
    else:
        return BlockData(
            "minecraft:redstone_wall_torch",
            [("lit", bool_to_str(lit)), ("facing", facing)],
        )
