import copy
from contextlib import suppress

from nbt.nbt import NBTFile, TAG_Compound, TAG_Int, TAG_List, TAG_String

from .blocks import BlockData
from .items import Inventory
from .shapes import Cuboid, Vector, Volume

AIR_BLOCK = BlockData("minecraft:air")
DATAVERSION = 3218


class Palette:
    """Holds distinct list of blocks used in structure. BlockPosition 'state' refers to index from this list.

    Methods:
        try_append(block):
            adds a block if not in palette
        extend(blocks):
            adds any blocks not in palette
        get_state(block):
            return index of state that matches block
        try_get_state(block):
            return None or index of block
        get_nbt():
            return TAG_List representation of palette
    """

    __blocks: "list[BlockData]"

    def __init__(self, block_data: "list[BlockData]" = []) -> None:
        self.__blocks = [b.copy() for b in block_data]

    def __iter__(self) -> iter:
        return iter(self.__blocks)

    def __getitem__(self, key) -> BlockData:
        return self.__blocks[key]

    def try_append(self, block: BlockData) -> None:
        if block is None:
            raise ValueError("Palette cannont contain None")
        if block not in self.__blocks:
            self.__blocks.append(block)

    def copy(self) -> None:
        return Palette(self.__blocks)

    def extend(self, blocks: "list[BlockData]") -> None:
        for block in blocks:
            self.try_append(block)

    def get_state(self, block: BlockData) -> int:
        return self.__blocks.index(block)

    def try_get_state(self, block: BlockData) -> int:
        try:
            return self.__blocks.index(block)
        except ValueError:
            return None

    def get_nbt(self) -> TAG_List:
        nbt_list = TAG_List(name="palette", type=TAG_Compound)
        for block in self.__blocks:
            nbt_list.tags.append(block.get_nbt())
        return nbt_list

    def reflect(self, reflector: Vector) -> None:
        for block in self.__blocks:
            block.reflect(
                reflector.x is not None,
                reflector.y is not None,
                reflector.z is not None,
            )


class BlockPosition:
    """For use in NBTStructure. Stores block position, state from Palette, and inventory."""

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
        self.pos = pos.copy()
        self.state = state
        self.inv = None if inventory is None else inventory.copy()
        self.other_nbt = copy.deepcopy(other_nbt)

    def __hash__(self) -> int:
        return hash(self.pos)

    def get_nbt(self, block_name: str) -> TAG_Compound:
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
        new_inv = self.inv.copy() if self.inv else None
        return BlockPosition(
            pos=self.pos.copy(),
            state=self.state,
            inventory=new_inv,
            other_nbt=copy.deepcopy(self.other_nbt),
        )


class NBTStructure:
    """Stores and manipulates list of block positions and states. Generates NBT file that can be imported to Minecraft.

    Important Note:
        Air will overwrite blocks with empty space when cloned in code or loaded in MC. Empty voids will not.

    Get Methods:
        get_nbt(pressurize=True):
            Get NBT file object of structure. Input pressurize=True to replace empty voids with air, the same way Minecraft itself would save.
        get_block_state(pos) -> BlockData:
            Get BlockData at pos from palette
        get_block_inventory(pos) -> Inventory:
            Get Inventory of block at pos
        get_max_coords(include_air=True) -> Vector:
            Get max x,y,z found across all blocks
        get_min_coords(include_air=True) -> Vector:
            Get min x,y,z found across all blocks

    Fill Command Methods:
        set_block(pos, block, inv: Inventory = None) -> bool:
            Update block at position. Set as None to remove.
        fill(volume: list[Vector], fill_block: BlockData, inv: Inventory = None):
            Set all blocks in volume to fill_block.
        fill_hollow(self, volume: Cuboid, fill_block: BlockData, inv: Inventory = None):
            Fill all blocks along faces of cuboid to fill_block. Fill interior with air blocks.
        fill_keep(self, volume: list[Vector], fill_block: BlockData, inv: Inventory = None):
            Fill only air blocks and void spaces with fill_block. Leave others untouched.
        fill_replace( volume: list[Vector], fill_block: BlockData, filter_blocks: list[BlockData], inv: Inventory = None):
            Replace all instances of filter_block with fill_block in volume. Use None to target voids.

    Clone Command Methods:
        clone_block(s_pos:Vector, t_pos:Vector):
            Clones a single block from one pos to another.
        clone(volume: Cuboid, dest: Vector):
            Clone blocks contained in source volume. Input dest is min x,y,z of target volume. Overlap is not allowed.
        clone_structure(other: NBTStructure, dest: Vector):
            Clone another NBTStructure object into this one. Input dest is min x,y,z of target volume.

    Bulk Update Methods:
        translate(delta: Vector):
            Add delta vector to every block position.
        crop(volume: Cuboid):
            Remove blocks outside of volume
        pressurize():
            Replace all voids with air blocks
        depressurize():
            Replace all air blocks with voids
    """

    blocks: "dict[int, BlockPosition]"
    palette: Palette

    def __init__(self, filepath: str = None) -> None:
        if filepath is not None:
            nbt = NBTFile(filename=filepath)
            self.load_from_nbt(nbt)
        else:
            self.blocks = {}
            self.palette = Palette()

    def __getitem__(self, key) -> BlockPosition:
        return self.blocks.get(key, None)

    def copy(self, volume: "list[Vector]" = None) -> "NBTStructure":
        structure = NBTStructure()
        structure.blocks = {
            key: value.copy()
            for key, value in self.blocks.items()
            if volume is None or value.pos in volume
        }
        structure.palette = self.palette.copy()
        return structure

    def load_from_nbt(self, nbt: NBTFile) -> None:
        self.palette = Palette(
            [BlockData.load_from_nbt(t) for t in nbt["palette"].tags]
        )
        self.blocks = {}
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
            self.__set_block(block)

    def get_nbt(
        self, pressurize: bool = True, trim_excess_air: bool = False
    ) -> NBTFile:
        """Create NBTFile that can be saved to disk then loaded into Minecraft via a structure block. Default args will save like a structure block would.

        Args:
            pressurize (bool, optional):
                Replace voids with air blocks so that structure loads like one created in minecraft would, as a full cuboid. Defaults to True.
            trim_excess_air (bool, optional):
                minimize size of structure by restricting to smallest cuboid containing all non-air blocks. Defaults to False.

        Returns:
            NBTFile: the complete structure
        """
        working_copy = self.copy()
        min_coords = working_copy.get_min_coords(include_air=not trim_excess_air)
        max_coords = working_copy.get_max_coords(include_air=not trim_excess_air)
        if trim_excess_air:
            working_copy.crop(Cuboid(min_coords, max_coords))
        working_copy.translate(min_coords * -1)
        max_coords.sub(min_coords)
        min_coords.sub(min_coords)
        if pressurize:
            working_copy.pressurize(Cuboid(min_coords, max_coords))

        working_copy.cleanse_palette()
        structure_file = NBTFile()
        size = max_coords + Vector(1, 1, 1)
        structure_file.tags.append(size.get_nbt("size"))
        structure_file.tags.append(TAG_List(name="entities", type=TAG_Compound))
        nbt_blocks = TAG_List(name="blocks", type=TAG_Compound)
        for block in working_copy.blocks.values():
            nbt_blocks.tags.append(block.get_nbt(self.palette[block.state].name))
        structure_file.tags.append(nbt_blocks)
        structure_file.tags.append(working_copy.palette.get_nbt())
        structure_file.tags.append(TAG_Int(name="DataVersion", value=DATAVERSION))
        return structure_file

    def cleanse_palette(self) -> None:
        new_structure = NBTStructure()
        for b in self.blocks.values():
            new_structure.set_block(b.pos, self.palette[b.state], b.inv, b.other_nbt)
        self.blocks = new_structure.blocks
        self.palette = new_structure.palette

    def get_block_state(self, pos: Vector) -> BlockData:
        """Get block name and properties at pos"""
        block = self.__get_block(pos)
        return None if block is None else self.palette[block.state]

    def get_block_inventory(self, pos: Vector) -> Inventory:
        """Get inventory at pos"""
        block = self.__get_block(pos)
        return None if block is None else block.inv

    def get_block_other_nbt(self, pos: Vector) -> Inventory:
        """Get non-inventory block nbt at pos"""
        block = self.__get_block(pos)
        return None if block is None else block.other_nbt

    def __get_block(self, pos: Vector) -> BlockPosition:
        return self.blocks.get(pos, None)

    def set_block(
        self,
        pos: Vector,
        block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Update block at pos. Remove if block is None."""
        if block is None:
            return self.__remove_block(pos)
        state = self.__upsert_palette(block)
        return self.__set_block(BlockPosition(pos, state, inv, other_nbt))

    def __set_block(self, new_block: BlockPosition) -> None:
        self.blocks[new_block.pos] = new_block

    def __remove_block(self, pos: Vector) -> None:
        with suppress(KeyError):
            self.blocks.pop(pos)

    def __upsert_palette(self, new_block: BlockData) -> int:
        """adds block to palette and/or returns the state id"""
        if new_block is None:
            return None
        self.palette.try_append(new_block)
        return self.palette.get_state(new_block)

    def get_max_coords(self, include_air=True) -> Vector:
        """get max x,y,z of smallest cuboid containing all blocks"""
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
        """get min x,y,z of smallest cuboid containing all blocks"""
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
        """Add delta to every block's pos"""
        if delta == Vector(0, 0, 0):
            return
        new_blocks = {}
        for block in self.blocks.values():
            block.pos.add(delta)
            new_blocks[block.pos] = block
        self.blocks = new_blocks

    def reflect(self, reflector: Vector) -> None:
        """Mirror the structure on x, y, and z axis.

        Specify x,y,z values to reflect around. Use None for x,y,z to not reflect values on that axis.
        Update block states to swap north & south, east & west, up & down, etc.

        Example input: reflector = Vector(1,None,-2)
            :All Vector values of x = 1 stay the same, x==0 becomes 2, x==2 becomes 0, x==-1 becomes 3, etc.
            :All y values stay the same.
            :All Vector values of z = -2 stay the same, z==-3 becomes -1, z==-1 becomes 3, z==-4 becomes 0, etc.
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

    def clone_structure(self, other: "NBTStructure", dest: Vector) -> None:
        """Completely clone other structure to this one. dest defines minimum x,y,z corner of target volume"""
        for otherblock in other.blocks.values():
            dest_pos = otherblock.pos + dest
            self.set_block(
                dest_pos,
                other.palette[otherblock.state],
                otherblock.inv,
                otherblock.other_nbt,
            )

    def clone(self, source_volume: Volume, dest: Vector) -> None:
        """Clones blocks from source_volume. dest defines minimum x,y,z of target volume which must not overlap source."""
        if source_volume.would_clone_overlap(dest):
            raise ValueError("The source and destination volumes cannot overlap")
        offset = dest - source_volume.min_corner
        for pos in source_volume:
            self.clone_block(pos, pos + offset)

    def clone_block(self, s_pos: Vector, t_pos: Vector) -> None:
        """Clone a single block from s_pos to t_pos"""
        block = self.__get_block(s_pos)
        if block is None:
            return
        else:
            return self.__set_block(
                BlockPosition(t_pos, block.state, block.inv, block.other_nbt)
            )

    def crop(self, volume: Cuboid) -> None:
        """Remove blocks outside of volume

        Args:
            volume (Cuboid): defines corners of desired box
        """
        for k, v in self.blocks.copy().items():
            if not volume.contains(v.pos):
                self.blocks.pop(k)

    def size(self) -> Vector:
        if not any(self.blocks):
            return Vector(0, 0, 0)
        return Vector(1, 1, 1) + self.get_max_coords() - self.get_min_coords()

    def fill(
        self,
        volume: "list[Vector]",
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Set all blocks in volume to fill_block.

        Args:
            volume (list[Vector]): iterable with all positions contained in volume
            fill_block (BlockData): block to set. Use None to remove blocks.
            inv (Inventory): inventory to set, only if block is being set too.
        """
        new_state = self.__upsert_palette(fill_block)
        for pos in volume:
            if new_state is None:
                self.__remove_block(pos)
            else:
                self.__set_block(BlockPosition(pos, new_state, inv, other_nbt))

    def fill_hollow(
        self,
        volume: Volume,
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Fill all blocks on exterior with fill_block. Fill interior with air.

        Args:
            volume (Volume): gives list of exterior and interior positions to update
            fill_block (BlockData): block to set. Use None to remove blocks.
        """
        self.fill(volume.exterior(), fill_block, inv, other_nbt)
        self.fill(volume.interior(), AIR_BLOCK)

    def pressurize(self, volume: "list[Vector]" = None) -> None:
        """Fill all voids with air. Use this to make sure existing blocks are removed when loading into Minecraft or cloning."""
        if volume is None:
            volume = self.get_full_cuboid_volume()
        return self.fill_keep(volume, AIR_BLOCK)

    def depressurize(self, volume: "list[Vector]" = None) -> None:
        """Remove all air blocks in volume. This allows you to load in MC and clone without air overwriting existing blocks in target volume."""
        if volume is None:
            volume = self.get_full_cuboid_volume()
        return self.fill_keep(volume, None)

    def get_full_cuboid_volume(self, include_air=True) -> Cuboid:
        return Cuboid(
            self.get_min_coords(include_air), self.get_max_coords(include_air)
        )

    def fill_keep(
        self,
        volume: "list[Vector]",
        fill_block: BlockData,
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Fill only air blocks and void spaces with fill_block. Leave others untouched.

        Args:
            volume (list[Vector]):
                volume to search
            fill_block (BlockData):
                use fill_block = None to remove all air blocks
            inv (Inventory):
                inventory to be set for blocks
        """
        self.fill_replace(volume, fill_block, [None, AIR_BLOCK], inv, other_nbt)

    def fill_replace(
        self,
        volume: "list[Vector]",
        fill_block: BlockData,
        filter_blocks: "list[BlockData]",
        inv: Inventory = None,
        other_nbt: TAG_Compound = None,
    ) -> None:
        """Replace all instances of filter blocks with fill block in volume. Use None to target voids.
        Args:
            volume (list[Vector]):
                volume to search
            fill_block (BlockData):
                use fill_block = None to remove all air blocks
            filter_blocks "BlockData|list[BlockData]":
                List of block data to search for. Can include fill_block. Include None to fill empty space.
            inv (Inventory):
                inventory to be set for blocks
        """
        if not isinstance(filter_blocks, list) and (
            isinstance(filter_blocks, BlockData) or filter_blocks is None
        ):
            filter_blocks = [filter_blocks]

        filter_states = [self.palette.try_get_state(block) for block in filter_blocks]
        if not any(f is not None for f in filter_states) and None not in filter_blocks:
            return
        new_state = self.__upsert_palette(fill_block)

        for pos in volume:
            block = self.__get_block(pos)
            if block is None and None in filter_states:
                self.__set_block(BlockPosition(pos.copy(), new_state, inv, other_nbt))
            elif block is not None and block.state in filter_states:
                if new_state is None:
                    self.__remove_block(pos)
                else:
                    block.state = new_state
                    block.inv = None if inv is None else inv.copy()
                    block.other_nbt = copy.deepcopy(other_nbt)
