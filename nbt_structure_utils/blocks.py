from collections.abc import Iterable

from nbt.nbt import TAG_Compound, TAG_String

REFLECT_PROPS_X = [
    ("east", "west"),
    ("west", "east"),
    ("ascending_east", "ascending_west"),
    ("ascending_west", "ascending_east"),
    ("north_east", "north_west"),
    ("south_east", "south_west"),
    ("north_west", "north_east"),
    ("south_west", "south_east"),
    ("left", "right"),
    ("right", "left"),
    ("outer_left", "outer_right"),
    ("outer_right", "outer_left"),
]
REFLECT_PROPS_Y = [
    ("up", "down"),
    ("down", "up"),
    ("top", "bottom"),
    ("bottom", "top"),
    ("ceiling", "floor"),
    ("floor", "ceiling"),
    ("ascending_north", "ascending_south"),
    ("ascending_south", "ascending_north"),
    ("ascending_east", "ascending_west"),
    ("ascending_west", "ascending_east"),
]
REFLECT_PROPS_Z = [
    ("north", "south"),
    ("south", "north"),
    ("ascending_north", "ascending_south"),
    ("ascending_south", "ascending_north"),
    ("north_east", "south_east"),
    ("south_east", "north_east"),
    ("north_west", "south_west"),
    ("south_west", "north_west"),
    ("left", "right"),
    ("right", "left"),
]


class BlockData:
    """Stores block name and state. Can read and create NBT.

    Attributes:
        name : str
            The block's name in minecraft.
        properties : list[tuple(str, str)]
            A list of the block's properties, as seen from F3.

    Methods:
        copy(): Create a copy of self.
        reflect(reflector): Reflect block states across specified planes.
        get_nbt(): Create an NBT equivalent of self.

    Static Methods:
        load_from_nbt(nbt): Create a new object from NBT.
    """

    name: str
    properties: "list[tuple]"

    __rotation = ["_head", "_sign", "_banner"]
    __not_rotation = ["_wall_sign"]

    def __init__(self, item_id: str, props: "Iterable[tuple]" = []) -> None:
        if ":" not in item_id:
            self.name = "minecraft:" + item_id
        else:
            self.name = item_id
        self.properties = [(p[0], p[1]) for p in props]

    def __eq__(self, __o: object) -> bool:
        if __o is None:
            return False
        return self.name == __o.name and sorted(self.properties) == sorted(
            __o.properties
        )

    def copy(self) -> "BlockData":
        """Create a copy of self."""
        return BlockData(self.name, self.properties)

    def reflect(self, reflect_x: bool, reflect_y: bool, reflect_z: bool) -> None:
        """Update block state to swap north & south, up & down, etc."""
        if self.__uses_rotation_prop():
            self.__reflect_rotation_prop(reflect_x, reflect_z)
        if self.properties:
            if reflect_x:
                self.__reflect_states(REFLECT_PROPS_X)
            if reflect_y:
                self.__reflect_states(REFLECT_PROPS_Y)
            if reflect_z:
                self.__reflect_states(REFLECT_PROPS_Z)

    def __reflect_states(self, state_pairs) -> None:
        if self.name.endswith("_wall"):
            state_pairs = [p for p in state_pairs if p[0] != "up"]
        self.properties = [
            (
                next((v[1] for v in state_pairs if prop[0] == v[0]), prop[0]),
                next((v[1] for v in state_pairs if prop[1] == v[0]), prop[1]),
            )
            for prop in self.properties
        ]

    def __uses_rotation_prop(self) -> bool:
        return any(
            postfix for postfix in self.__rotation if self.name.endswith(postfix)
        ) and not any(
            postfix for postfix in self.__not_rotation if self.name.endswith(postfix)
        )

    def __reflect_rotation_prop(self, reflect_x: bool, reflect_z: bool) -> None:
        rotation = next((int(p[1]) for p in self.properties if p[0] == "rotation"), 0)
        if reflect_x:
            rotation = (16 - rotation) % 16
        if reflect_z:
            rotation = (24 - rotation) % 16
        self.properties = [p for p in self.properties if p[0] != "rotation"]
        self.properties.append(("rotation", rotation))

    def get_nbt(self) -> TAG_Compound:
        """Create an NBT equivalent of self."""
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
        """Load from NBT to new object."""
        name = nbt["Name"].value
        properties = []
        if "Properties" in nbt:
            properties = [(p.name, p.value) for p in nbt["Properties"].tags]
        return BlockData(name, properties)
