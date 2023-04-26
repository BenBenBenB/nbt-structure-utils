from collections.abc import Iterable

from nbt.nbt import TAG_Compound, TAG_String

from .block_state_transformations import (
    BLOCK_SUFFIXES_FACE_ALLOW,
    BLOCK_SUFFIXES_ROTATION_ALLOW,
    BLOCK_SUFFIXES_ROTATION_FORBID,
    REFLECT_PROPS_X,
    REFLECT_PROPS_Y,
    REFLECT_PROPS_Z,
    ROTATE_PROPS_X_90,
    ROTATE_PROPS_Y_90,
    ROTATE_PROPS_Z_90,
)

X_AXIS, Y_AXIS, Z_AXIS = "x", "y", "z"
NORTH, SOUTH, EAST, WEST = "north", "south", "east", "west"
WALL, FLOOR, CEILING = "wall", "floor", "ceiling"


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
        """Update block state to swap north & south, up & down, etc.

        Some blocks do not have true reflections over the y-axis. Beware of:
            rail, torch, banner, carpet, pressure plate, bed, plants, etc.
        """
        prop_map = []
        if self.properties:
            if reflect_x:
                prop_map.extend(REFLECT_PROPS_X)
            if reflect_y:
                prop_map.extend(REFLECT_PROPS_Y)
            if reflect_z:
                prop_map.extend(REFLECT_PROPS_Z)
            self.__transform_states(prop_map)
        if self.__uses_rotation_prop():
            self.__reflect_rotation_prop(reflect_x, reflect_z)

    def __transform_states(self, state_pairs) -> None:
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
            suffix
            for suffix in BLOCK_SUFFIXES_ROTATION_ALLOW
            if self.name.endswith(suffix)
        ) and not any(
            suffix
            for suffix in BLOCK_SUFFIXES_ROTATION_FORBID
            if self.name.endswith(suffix)
        )

    def __reflect_rotation_prop(self, reflect_x: bool, reflect_z: bool) -> None:
        rotation = next((int(p[1]) for p in self.properties if p[0] == "rotation"), 0)
        if reflect_x:
            rotation = (16 - rotation) % 16
        if reflect_z:
            rotation = (24 - rotation) % 16
        self.properties = [p for p in self.properties if p[0] != "rotation"]
        self.properties.append(("rotation", rotation))

    def rotate(self, axis: str, angle: int) -> None:
        """Update block state to rotate by angle about input axis.

        Some blocks can't truly rotate states for x and z axis rotations of 90 or 270 degrees:
            Beware of banners, doors, torches, rails. slabs, fences, stairs, dripstone, plants, etc.

        Args:
            axis (str): x, y, or z
            angle (int): A multiple of 90
        """
        if axis not in [X_AXIS, Y_AXIS, Z_AXIS]:
            raise ValueError("Must choose valid axis.")
        if not angle % 90 == 0:
            raise ValueError("Must choose multiple of 90 degrees.")

        angle = angle % 360
        prop_map = []
        # 180 degree rotations need no special rules.
        if angle == 180:
            self.__rotate_props_180(axis)
        # y-axis rotations need no special rules besides rotation prop.
        elif axis == Y_AXIS:
            if angle == 90:
                prop_map = ROTATE_PROPS_Y_90
            elif angle == 270:
                prop_map = [(p[1], p[0]) for p in ROTATE_PROPS_Y_90]
            if self.__uses_rotation_prop():
                self.__rotate_rotation_prop(angle)
        # x and z-axis rotations may need special rules for some blocks.
        else:
            prop_map = self.__get_rotation_state_mappings(axis, angle)

        self.__transform_states(prop_map)

    def __get_rotation_state_mappings(
        self, axis: str, angle: int
    ) -> "list[tuple[str,str]]":
        """Determine how this block's states need to change for x and z rotations.

        Args:
            axis (str): x or z axis
            angle (int): 90 or 270 degrees
        """

        prop_map = self.__get_special_rotation(axis, angle)
        if not prop_map and self.properties:
            if axis == X_AXIS:
                prop_map = ROTATE_PROPS_X_90
            elif axis == Y_AXIS:
                prop_map = ROTATE_PROPS_Y_90
            elif axis == Z_AXIS:
                prop_map = ROTATE_PROPS_Z_90
            if angle == 270:
                prop_map = [(p[1], p[0]) for p in prop_map]
        return prop_map

    def __get_special_rotation(self, axis, angle) -> "list[tuple[str, str]]":
        if any(self.name.endswith(suffix) for suffix in BLOCK_SUFFIXES_FACE_ALLOW):
            return self.__get_face_prop_maps(axis, angle)

        return []

    def __get_face_prop_maps(self, axis: str, angle: int) -> "list[tuple[str,str]]":
        prop_map = []
        curr_facing = next((p[1] for p in self.properties if p[0] == "facing"), None)
        curr_face = next((p[1] for p in self.properties if p[0] == "face"), FLOOR)
        if not curr_facing:
            # pick an arbitrary direction
            curr_facing = EAST
            self.properties.append("facing", curr_facing)
        if curr_face == FLOOR:
            prop_map.append((FLOOR, WALL))
        if curr_face == CEILING:
            prop_map.append((CEILING, WALL))

        if axis == X_AXIS:
            prop_map.extend(self.__get_face_props_x(angle, curr_facing, curr_face))
        elif axis == Z_AXIS:
            prop_map.extend(self.__get_face_props_z(angle, curr_facing, curr_face))
        return prop_map

    def __get_face_props_x(
        self, angle, curr_facing, curr_face
    ) -> "list[tuple[str,str]]":
        prop_map = []
        if curr_face == WALL:
            if curr_facing == SOUTH:
                if angle == 90:
                    prop_map.append((WALL, CEILING))
                else:
                    prop_map.append((WALL, FLOOR))
            elif curr_facing == NORTH:
                if angle == 90:
                    prop_map.append((WALL, FLOOR))
                else:
                    prop_map.append((WALL, CEILING))
        elif curr_face == FLOOR:
            if angle == 90:
                prop_map.append((curr_facing, SOUTH))
            else:
                prop_map.append((curr_facing, NORTH))
        elif curr_face == CEILING:
            if angle == 90:
                prop_map.append((curr_facing, NORTH))
            else:
                prop_map.append((curr_facing, SOUTH))
        return prop_map

    def __get_face_props_z(
        self, angle, curr_facing, curr_face
    ) -> "list[tuple[str,str]]":
        prop_map = []
        if curr_face == WALL:
            if curr_facing == WEST:
                if angle == 90:
                    prop_map.append((WALL, CEILING))
                else:
                    prop_map.append((WALL, FLOOR))
            elif curr_facing == EAST:
                if angle == 90:
                    prop_map.append((WALL, FLOOR))
                else:
                    prop_map.append((WALL, CEILING))
        elif curr_face == FLOOR:
            if angle == 90:
                prop_map.append((curr_facing, WEST))
            else:
                prop_map.append((curr_facing, EAST))
        elif curr_face == CEILING:
            if angle == 90:
                prop_map.append((curr_facing, EAST))
            else:
                prop_map.append((curr_facing, WEST))
        return prop_map

    def __rotate_rotation_prop(self, angle: int) -> None:
        """Handle update for "rotation" prop only."""
        rotation = next((int(p[1]) for p in self.properties if p[0] == "rotation"), 0)
        rotation = (rotation - 4 * (angle // 90)) % 16
        self.properties = [p for p in self.properties if p[0] != "rotation"]
        self.properties.append(("rotation", rotation))

    def __rotate_props_180(self, axis: str) -> None:
        """Reflecting along other 2 axes is equivalent to a 180 about input axis"""
        return self.reflect(axis != X_AXIS, axis != Y_AXIS, axis != Z_AXIS)

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
