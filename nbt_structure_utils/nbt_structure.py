import copy
from collections.abc import Iterable
from contextlib import suppress

import numpy as np
from nbt.nbt import NBTFile, TAG_Compound, TAG_Int, TAG_List, TAG_String

from .blocks import X_AXIS, Y_AXIS, Z_AXIS, BlockData
from .items import Inventory
from .shapes import Cuboid, IVolume, Vector

AIR_BLOCK = BlockData("minecraft:air")
EMPTY_SPACE = None
DATAVERSION = 3218


class Palette:
    """Holds distinct list of blocks used in structure. BlockPosition 'state' refers to index from this list.

    Methods:
        get_state(block): Get index of state that matches block.
        try_get_state(block): Get index of state that matches block, else None.
        try_append(block): Add block if not in palette.
        extend(blocks): Adds any blocks not in palette.
        copy(): Return a copy of this palette.
        reflect(reflector): Reflect block states across different planes.
        rotate(axis, angle): Rotate all states by angle around specified axis.
        get_nbt(): Get TAG_List representation of palette.
    """

    __blocks: "list[BlockData]"

    def __init__(self, block_data: "Iterable[BlockData]" = []) -> None:
        self.__blocks = [b.copy() for b in block_data]

    def __iter__(self) -> iter:
        return iter(self.__blocks)

    def __getitem__(self, key) -> BlockData:
        return self.__blocks[key]

    def try_append(self, block: BlockData) -> None:
        """Add block if not in palette

        Args:
            block (BlockData): _description_

        Raises:
            ValueError: _description_
        """
        if block is EMPTY_SPACE:
            raise ValueError("Palette cannont contain None")
        if block not in self.__blocks:
            self.__blocks.append(block)

    def copy(self) -> None:
        """Create and return a copy of this palette."""
        return Palette(self.__blocks)

    def extend(self, blocks: "Iterable[BlockData]") -> None:
        """Adds any blocks not in palette.

        Args:
            blocks (Iterable[BlockData]): list of block states
        """
        for block in blocks:
            self.try_append(block)

    def get_state(self, block: BlockData) -> int:
        """Get index of state that matches block.

        Args:
            block (BlockData): state to search for

        Returns:
            int: id corresponding to input state
        """
        return self.__blocks.index(block)

    def try_get_state(self, block: BlockData) -> int:
        """Get index of state that matches block, or return None.

        Args:
            block (BlockData): state to search for

        Returns:
            int: id corresponding to input state, or None
        """
        try:
            return self.__blocks.index(block)
        except ValueError:
            return None

    def get_nbt(self) -> TAG_List:
        """Get TAG_List representation of palette.

        Returns:
            TAG_List: NBT representing self.
        """
        nbt_list = TAG_List(name="palette", type=TAG_Compound)
        for block in self.__blocks:
            nbt_list.tags.append(block.get_nbt())
        return nbt_list

    def reflect(self, reflector: Vector) -> None:
        """Reflect block states across different planes.

        Args:
            reflector (Vector): determines which reflectable block states are updated.
        """
        for block in self.__blocks:
            block.reflect(
                reflector.x is not None,
                reflector.y is not None,
                reflector.z is not None,
            )

    def rotate(self, axis: str, angle: int) -> None:
        """Rotate all states by angle around specified axis.

        Args:
            axis (str): The axis to rotate around
            angle (int): The angle in degrees.
        """
        for block in self.__blocks:
            block.rotate(axis, angle)


class BlockPosition:
    """For use in NBTStructure. Stores block position, state from Palette, and inventory.

    Attributes:
        pos (Vector): x,y,z location of block.
        state (int): state id from the palette.
        inv (Inventory): inventory data.
        other_nbt (TAG_Compound): non-inventory NBT.

    Methods:
        get_nbt(block_name): Get NBT representation of self.
        copy(): Create a copy of self.
    """

    pos: Vector
    state: int  # from Palette
    inv: Inventory
    other_nbt: TAG_Compound

    def __init__(
        self,
        pos: Vector,
        state: int,
        inventory: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Create a new record of a block's data.

        Args:
            pos (Vector): x,y,z location of block.
            state (int): state id from the palette.
            inv (Inventory): inventory data.
            other_nbt (TAG_Compound): non-inventory NBT.
        """
        self.pos = pos.copy()
        self.state = state
        self.inv = None if inventory is None else inventory.copy()
        self.other_nbt = copy.deepcopy(other_nbt)

    def __hash__(self) -> int:
        return hash(self.pos)

    def get_nbt(self, block_name: str) -> TAG_Compound:
        """Get the NBT for a block matching self.

        Args:
            block_name (str): input for saving inventory container name.

        Returns:
            TAG_Compound: NBT representing self.
        """
        nbt_block = TAG_Compound()
        if any(i for i in [self.inv, self.other_nbt] if i is not None):
            nbt_block_nbt = TAG_Compound(name="nbt")
            if self.inv is not None:
                nbt_block_nbt.tags.append(self.inv.get_nbt())
                nbt_block_nbt.tags.append(TAG_String(name="id", value=block_name))
            if self.other_nbt is not None:
                nbt_block_nbt.tags.extend(self.other_nbt.tags)
            nbt_block.tags.append(nbt_block_nbt)
        nbt_block.tags.append(self.pos.get_nbt("pos"))
        nbt_block.tags.append(TAG_Int(name="state", value=self.state))

        return nbt_block

    def copy(self) -> "BlockPosition":
        """Create a copy of self."""
        new_inv = self.inv.copy() if self.inv else None
        return BlockPosition(
            pos=self.pos.copy(),
            state=self.state,
            inventory=new_inv,
            other_nbt=copy.deepcopy(self.other_nbt),
        )


class NBTStructure:
    """Stores and manipulates list of block positions and states. Generates NBT file that can be imported to Minecraft.

    Important Note: Air will overwrite blocks with empty space when cloned in code or loaded in MC. Empty spaces will not.

    Attributes:
        blocks : dict[int, BlockPosition]
            all the blocks and their data
        palette : Palette
            the block states

    Get Methods:
        get_nbt(pressurize, trim_excess_air):
            Get NBT file object of structure.
        get_block_state(pos):
            Get BlockData at pos from palette.
        get_block_inventory(pos):
            Get Inventory of block at pos.
        get_block_other_nbt(pos):
            Get Non-inventory NBT of block at pos.
        get_max_coords(include_air):
            Get max x,y,z found across all blocks.
        get_min_coords(include_air):
            Get min x,y,z found across all blocks.

    Fill Command Methods:
        set_block(pos, block, inv, other_nbt):
            Update block at position. Set as None to remove.
        fill(volume, fill_block, inv, other_nbt):
            Set all blocks in volume to fill_block.
        fill_hollow(self, volume, fill_block, inv, other_nbt):
            Fill all blocks along faces of cuboid to fill_block. Fill interior with air blocks.
        fill_keep(self, volume, fill_block, inv, other_nbt):
            Fill only air blocks and empty spaces with fill_block. Leave others untouched.
        fill_replace( volume, fill_block, filter_blocks, inv, other_nbt):
            Replace all instances of filter_blocks with fill_block in volume. Use None to target empty space.

    Clone Command Methods:
        clone_block(s_pos, t_pos):
            Clones a single block from one pos to another.
        clone(volume, dest):
            Clone blocks contained in source volume. Overlap is not allowed.
        clone_structure(other, dest, source_volume):
            Clone all or part of another NBTStructure object into this one.

    Bulk Update Methods:
        crop(volume):
            Remove blocks outside of volume.
        translate(delta):
            Move entire structure by some distance.
        reflect(reflector):
            Mirror the structure over specific planes.
        rotate(axis, angle):
            Rotate all positions and states by angle around specified axis
        pressurize(volume):
            Replace all empty spaces with air blocks.
        depressurize(volume):
            Replace all air blocks with empty spaces.

    Static Methods:
        load_from_nbt(nbt): Loads an NBT file from disk into self.
    """

    blocks: "dict[int, BlockPosition]"
    palette: Palette

    def __init__(self, filepath: str = None) -> None:
        """Create a new object and optionally load it with data from disk.

        Args:
            filepath (str, optional): location of .nbt file to load. Defaults to None.
        """
        if filepath is not None:
            nbt = NBTFile(filename=filepath)
            new_structure = NBTStructure.load_from_nbt(nbt)
            self.__dict__.update(new_structure.__dict__)
        else:
            self.blocks = {}
            self.palette = Palette()

    def __getitem__(self, key) -> BlockPosition:
        return self.blocks.get(key, None)

    def copy(self, volume: "Iterable[Vector]" = None) -> "NBTStructure":
        """Create a new copy of all or part of self.

        Args:
            volume (Iterable[Vector], optional): Positions to allow in the copy. Defaults to None.

        Returns:
            NBTStructure: A copy of self.
        """
        structure = NBTStructure()
        structure.blocks = {
            key: value.copy()
            for key, value in self.blocks.items()
            if volume is None or value.pos in volume
        }
        structure.palette = self.palette.copy()
        return structure

    @staticmethod
    def load_from_nbt(nbt: NBTFile) -> None:
        """Loads an NBT file from disk into self.

        Args:
            nbt (NBTFile): The NBT file to read.

        Returns:
            NBTStructure : An object representing the NBT file.
        """
        structure = NBTStructure()
        structure.palette = Palette(
            [BlockData.load_from_nbt(t) for t in nbt["palette"].tags]
        )
        structure.blocks = {}
        for b in nbt["blocks"].tags:
            pos = Vector.load_from_nbt(b["pos"])
            inv = None
            other_nbt = None
            if "nbt" in b:
                inv = Inventory.load_from_nbt(b["nbt"])
                other_nbt = b["nbt"]
                if inv is not None:
                    other_nbt.tags = [
                        t for t in other_nbt.tags if t.name not in ["Items", "id"]
                    ]
                if not other_nbt.tags:
                    other_nbt = None
            block = BlockPosition(pos, b["state"].value, inv, other_nbt)
            structure.__set_block(block)
        return structure

    def get_nbt(
        self,
        pressurize: bool = True,
        trim_excess_air: bool = False,
        align_to_origin: bool = True,
    ) -> NBTFile:
        """Create NBTFile representation of self.

        Can be saved to disk then loaded into Minecraft via a structure block. Default args will save like a structure block would.

        Args:
            pressurize (bool, optional): Replace empty space with air blocks. Defaults to True.
            trim_excess_air (bool, optional): Minimize size by removing air outside of smallest cuboid. Defaults to False.
            align_to_origin (bool, optional): Move all blocks so that the minimum corner is at 0,0,0

        Returns:
            NBTFile: the complete NBT representation of the structure.
        """
        # prepare and clean up copy
        working_copy = self.copy()
        min_coords = working_copy.get_min_coords(include_air=not trim_excess_air)
        max_coords = working_copy.get_max_coords(include_air=not trim_excess_air)
        if trim_excess_air:
            working_copy.crop(Cuboid(min_coords, max_coords))
        if pressurize:
            working_copy.pressurize(Cuboid(min_coords, max_coords))
        if align_to_origin:
            working_copy.translate(min_coords * -1)
        working_copy.cleanse_palette()

        # generate file from copy
        structure_file = NBTFile()
        size = max_coords - min_coords + Vector(1, 1, 1)
        structure_file.tags.append(size.get_nbt("size"))
        structure_file.tags.append(TAG_List(name="entities", type=TAG_Compound))
        nbt_blocks = TAG_List(name="blocks", type=TAG_Compound)
        for block in working_copy.blocks.values():
            nbt_blocks.tags.append(
                block.get_nbt(working_copy.palette[block.state].name)
            )
        structure_file.tags.append(nbt_blocks)
        structure_file.tags.append(working_copy.palette.get_nbt())
        structure_file.tags.append(TAG_Int(name="DataVersion", value=DATAVERSION))
        return structure_file

    def cleanse_palette(self) -> None:
        """Remove any unused blocks from the palette."""
        new_structure = NBTStructure()
        for b in self.blocks.values():
            new_structure.set_block(b.pos, self.palette[b.state], b.inv, b.other_nbt)
        self.blocks = new_structure.blocks
        self.palette = new_structure.palette

    def get_block_state(self, pos: Vector) -> BlockData:
        """Get block name and properties at pos.

        Args:
            pos (Vector): x, y, z position to search.

        Returns:
            BlockData: block name and properties at pos.
        """
        block = self.__get_block(pos)
        return None if block is EMPTY_SPACE else self.palette[block.state]

    def get_block_inventory(self, pos: Vector) -> Inventory:
        """Get block inventory at pos.

        Args:
            pos (Vector): x, y, z position to search.

        Returns:
            Inventory: Inventory at pos, if any.
        """
        block = self.__get_block(pos)
        return None if block is EMPTY_SPACE else block.inv

    def get_block_other_nbt(self, pos: Vector) -> TAG_Compound:
        """Get non-inventory block nbt at pos.

        Args:
            pos (Vector): x, y, z position to search.

        Returns:
            Inventory: Block nbt at pos, if any.
        """
        block = self.__get_block(pos)
        return None if block is EMPTY_SPACE else block.other_nbt

    def __get_block(self, pos: Vector) -> BlockPosition:
        return self.blocks.get(pos, None)

    def set_block(
        self,
        pos: Vector,
        block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Update block at pos. Remove if block is None.

        Args:
            pos (Vector): Location to place block.
            block (BlockData): Block's name and state to save in palette.
            inv (Inventory, optional): Inventory to be set. Defaults to None.
            other_nbt (TAG_Compound, optional):  Non-inventory NBT data to be set. Defaults to None.
        """
        if block is EMPTY_SPACE:
            return self.__remove_block(pos)
        state = self.__upsert_palette(block)
        return self.__set_block(BlockPosition(pos, state, inv, other_nbt))

    def __set_block(self, new_block: BlockPosition) -> None:
        self.blocks[new_block.pos] = new_block

    def __remove_block(self, pos: Vector) -> None:
        with suppress(KeyError):
            self.blocks.pop(pos)

    def __upsert_palette(self, new_block: BlockData) -> int:
        """Adds block to palette and/or returns the state id.

        Parameters:
            new_block (BlockData): Block's name and state to save in palette.

        Returns:
            int: Integer value corresponding to the block state.
        """
        if new_block is EMPTY_SPACE:
            return None
        self.palette.try_append(new_block)
        return self.palette.get_state(new_block)

    def get_max_coords(self, include_air=True) -> Vector:
        """Get maximum x,y,z of smallest cuboid containing all blocks.

        Args:
            include_air (bool, optional): Allows air blocks in search. Defaults to True.

        Returns:
            Vector: Max x, y, and z values found in structure.
        """
        if not self.blocks:
            return Vector(0, 0, 0)
        filter_state = None if include_air else self.palette.try_get_state(AIR_BLOCK)
        first = next(iter(self.blocks.values())).pos
        x, y, z = first.x, first.y, first.z
        for block in (b for b in self.blocks.values() if b.state != filter_state):
            if block.pos.x > x:
                x = block.pos.x
            if block.pos.y > y:
                y = block.pos.y
            if block.pos.z > z:
                z = block.pos.z
        return Vector(x, y, z)

    def get_min_coords(self, include_air=True) -> Vector:
        """Get minimum x,y,z of smallest cuboid containing all blocks.

        Args:
            include_air (bool, optional): Allows air blocks in search. Defaults to True.

        Returns:
            Vector: Max x, y, and z values found in structure.
        """
        if not self.blocks:
            return Vector(0, 0, 0)
        filter_state = None if include_air else self.palette.try_get_state(AIR_BLOCK)
        first = next(iter(self.blocks.values())).pos
        x, y, z = first.x, first.y, first.z
        for block in (b for b in self.blocks.values() if b.state != filter_state):
            if block.pos.x < x:
                x = block.pos.x
            if block.pos.y < y:
                y = block.pos.y
            if block.pos.z < z:
                z = block.pos.z
        return Vector(x, y, z)

    def translate(self, delta: Vector) -> None:
        """Move entire structure by some distance.

        Parameters:
            delta (Vector): x,y,z values to add to every position in structure.
        """
        if delta == Vector(0, 0, 0):
            return
        new_blocks = {}
        for block in self.blocks.values():
            block.pos.add(delta)
            new_blocks[block.pos] = block
        self.blocks = new_blocks

    def reflect(self, reflector: Vector) -> None:
        """Mirror the structure over specific planes.

        Swap blocks around and update states to swap north & south, up & down, etc.

        Parameters:
            reflector (Vector): x,y,z values to reflect around. Use None to not reflect on that axis.

        Example input: reflector = Vector(1,None,-2)
            x: values at x = 1 stay the same, x=0 becomes 2, x=2 becomes 0, x=-1 becomes 3, etc.
            y: values stay the same.
            z: values at z = -2 stay the same, z=-3 becomes -1, z=-1 becomes 3, z=-4 becomes 0, etc.
        """
        if reflector == Vector(None, None, None):
            return
        reflection: "dict(int,BlockPosition)" = {}
        for block in self.blocks.values():
            new_pos = self.__get_reflected_pos(block.pos, reflector)
            block.pos = new_pos
            reflection[new_pos] = block
        self.blocks = reflection
        self.palette.reflect(reflector)

    def __get_reflected_pos(self, pos: Vector, reflector: Vector) -> Vector:
        new_pos = pos.copy()
        if reflector.x is not None:
            new_pos.x = 2 * reflector.x - pos.x
        if reflector.y is not None:
            new_pos.y = 2 * reflector.y - pos.y
        if reflector.z is not None:
            new_pos.z = 2 * reflector.z - pos.z
        return new_pos

    def rotate(self, axis: str, angle: int) -> None:
        """Rotate the blocks and states around an axis by an angle.

        The positive angle direction is determined by the right-hand rule, unlike Minecraft.
        This means 90 degrees here is 270 in the structure block UI and vice versa.
        Facing directly east (+x), up (+y), or south (+z), positive rotation is clockwise.

        Parameters:
            axis(str): Choose to rotate around the x,y or z azis.
            angle(int): Rotation angle, in degrees. Must be multiple of 90.
        """
        if axis not in [X_AXIS, Y_AXIS, Z_AXIS]:
            raise ValueError("Must choose valid axis")
        if not angle % 90 == 0:
            raise ValueError("Must choose multiple of 90 degrees.")
        angle = angle % 360
        if angle == 0:
            return
        rotation: "dict(int,BlockPosition)" = {}
        for block in self.blocks.values():
            new_pos = self.__get_rotated_pos(block.pos, axis, angle)
            block.pos = new_pos
            rotation[new_pos] = block
        self.blocks = rotation
        self.palette.rotate(axis, angle)

    def __get_rotated_pos(self, pos: Vector, axis: str, angle: int) -> Vector:
        """Hit it with a rotation matrix."""
        original_pos = np.array((pos.x, pos.y, pos.z))
        theta = np.radians(angle)
        c, s = np.cos(theta), np.sin(theta)
        if axis == X_AXIS:
            rotation_matrix = np.array([(1, 0, 0), (0, c, -s), (0, s, c)], dtype=int)
        if axis == Y_AXIS:
            rotation_matrix = np.array([(c, 0, s), (0, 1, 0), (-s, 0, c)], dtype=int)
        if axis == Z_AXIS:
            rotation_matrix = np.array([(c, -s, 0), (s, c, 0), (0, 0, 1)], dtype=int)
        new_pos = np.matmul(rotation_matrix, original_pos)
        return Vector(new_pos[0], new_pos[1], new_pos[2])

    def clone_structure(
        self,
        other: "NBTStructure",
        dest: Vector,
        source_volume: "Iterable[Vector]" = None,
    ) -> None:
        """Clone blocks from another structure to this one.

        Args:
            other (NBTStructure): Structure from which to clone blocks.
            dest (Vector): Position in self that corresponds to 0,0,0 in other structure.
            source_volume (Iterable[Vector], optional): Restricts positions to copy from other. Defaults to None.
        """
        for otherblock in other.blocks.values():
            if source_volume is None or otherblock.pos in source_volume:
                dest_pos = otherblock.pos + dest
                self.set_block(
                    dest_pos,
                    other.palette[otherblock.state],
                    otherblock.inv,
                    otherblock.other_nbt,
                )

    def clone(self, source_volume: IVolume, dest: Vector) -> None:
        """Clones blocks from self. dest defines minimum x,y,z of target volume. Must not overlap source volume.

        Args:
            source_volume (IVolume): Position of block to copy.
            dest (Vector): Position of block to update.

        Raises:
            ValueError: Overlap error.
        """
        if source_volume.would_clone_overlap(dest):
            raise ValueError("The source and destination volumes cannot overlap")
        offset = dest - source_volume.min_corner
        for pos in source_volume:
            self.clone_block(pos, pos + offset)

    def clone_block(self, s_pos: Vector, t_pos: Vector) -> None:
        """Clone a single block.

        Args:
            s_pos (Vector): Position of block to copy.
            t_pos (Vector): Position of block to update.
        """
        block = self.__get_block(s_pos)

        return (
            None
            if block is EMPTY_SPACE
            else self.__set_block(
                BlockPosition(t_pos, block.state, block.inv, block.other_nbt)
            )
        )

    def crop(self, volume: "Iterable[Vector]") -> None:
        """Remove all blocks outside of input positions.

        Args:
            volume (Iterable[Vector]): Gives list of positions that will remain.
        """
        for k, v in self.blocks.copy().items():
            if not volume.contains(v.pos):
                self.blocks.pop(k)

    def size(self) -> Vector:
        """Get the length of the 3 sides of the smallest cuboid that contains all blocks.

        Returns:
            Vector: x, y, and z side lengths of the structure.
        """
        if not any(self.blocks):
            return Vector(0, 0, 0)
        return Vector(1, 1, 1) + self.get_max_coords() - self.get_min_coords()

    def fill(
        self,
        volume: "Iterable[Vector]",
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Set all blocks in volume to fill_block.

        Args:
            volume (Iterable[Vector]): Positions to update.
            fill_block (BlockData): Block to set. Use None to remove blocks.
            inv (Inventory, optional): Inventory to set. Defaults to None.
            other_nbt (TAG_Compound, optional): Non-inventory NBT data. Defaults to None.
        """
        new_state = self.__upsert_palette(fill_block)
        for pos in volume:
            if new_state is EMPTY_SPACE:
                self.__remove_block(pos)
            else:
                self.__set_block(BlockPosition(pos, new_state, inv, other_nbt))

    def fill_hollow(
        self,
        volume: IVolume,
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Fill all blocks on exterior with fill_block. Fill interior with air.

        Args:
            volume (IVolume): Gives interior and exterior positions to update.
            fill_block (BlockData): Block to set. Use None to remove blocks.
            inv (Inventory, optional): Inventory to set. Defaults to None.
            other_nbt (TAG_Compound, optional): Non-inventory NBT data. Defaults to None.
        """
        self.fill(volume.exterior(), fill_block, inv, other_nbt)
        self.fill(volume.interior(), AIR_BLOCK)

    def pressurize(self, volume: "Iterable[Vector]" = None) -> None:
        """Fill all empty space with air.

        Use this to make sure existing blocks are removed when loading into Minecraft or cloning.

        Args:
            volume (Iterable[Vector], optional): Limits the positions that may be set to air. Defaults to None.
        """
        if volume is None:
            volume = self.get_full_cuboid_volume()
        return self.fill_keep(volume, AIR_BLOCK)

    def depressurize(self, volume: "Iterable[Vector]" = None) -> None:
        """Remove all air blocks.

        Args:
            volume (Iterable[Vector], optional): Limits the positions that may be removed. Defaults to None.
        """
        if volume is None:
            volume = self.get_full_cuboid_volume()
        return self.fill_keep(volume, None)

    def get_full_cuboid_volume(self, include_air=True) -> Cuboid:
        """Get the smallest cuboid that contains the full structure.

        Args:
            include_air (bool, optional): Allows air blocks in search. Defaults to True.

        Returns:
            Cuboid: A representation of the structure's volume.
        """
        return Cuboid(
            self.get_min_coords(include_air), self.get_max_coords(include_air)
        )

    def fill_keep(
        self,
        volume: "Iterable[Vector]",
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Fill only air blocks and empty spaces with fill_block. Leave others untouched.

        Args:
            volume (Iterable[Vector]): Positions to update.
            fill_block (BlockData): Block to set. Use None to remove blocks.
            inv (Inventory, optional): Inventory to set. Defaults to None.
            other_nbt (TAG_Compound, optional): Non-inventory NBT data. Defaults to None.
        """
        self.fill_replace(volume, fill_block, [None, AIR_BLOCK], inv, other_nbt)

    def fill_replace(
        self,
        volume: "Iterable[Vector]",
        fill_block: BlockData,
        filter_blocks: "Iterable[BlockData]",
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Replace all instances of filter blocks with fill block in volume. Use None to target empty space.

        Parameters:
            volume (Iterable[Vector]): Positions to update.
            fill_block (BlockData): Block to set. Use None to remove blocks.
            filter_blocks (Iterable[BlockData]): List of block data to search for. Can include fill_block. Include None to fill empty space
            inv (Inventory, optional): Inventory to set. Defaults to None.
            other_nbt (TAG_Compound, optional): Non-inventory NBT data. Defaults to None.
        """
        if not isinstance(filter_blocks, list) and (
            isinstance(filter_blocks, BlockData) or filter_blocks is EMPTY_SPACE
        ):
            filter_blocks = [filter_blocks]

        filter_states = [self.palette.try_get_state(block) for block in filter_blocks]
        if not any(f is not None for f in filter_states) and None not in filter_blocks:
            return
        new_state = self.__upsert_palette(fill_block)

        for pos in volume:
            block = self.__get_block(pos)
            if block is EMPTY_SPACE and None in filter_states:
                self.__set_block(BlockPosition(pos.copy(), new_state, inv, other_nbt))
            elif block is not None and block.state in filter_states:
                if new_state is EMPTY_SPACE:
                    self.__remove_block(pos)
                else:
                    block.state = new_state
                    block.inv = None if inv is None else inv.copy()
                    block.other_nbt = copy.deepcopy(other_nbt)
