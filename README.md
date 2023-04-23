# NBTStructureUtils

> A python library to create and edit NBT structure files for Minecraft.

This has been tested with Minecraft version 1.19.3.

**Features**

- Create, read, and edit NBT structure files.
- Methods inspired by Minecraft's fill, setblock, and clone commands.
- Edit the state, inventory, and NBT data of blocks.
- Special classes to help fill Cuboids and draw straight lines.

## Basic Usage
### Minecraft NBT Structure
This library creates .nbt files that can be placed in minecraft worlds. with a Structure Block or structure command. 

See the minecraft wiki for details on each:
- [Structure Block](https://minecraft.fandom.com/wiki/Structure_Block)
- [structure Command](https://minecraft.fandom.com/wiki/Commands/structure)


### Edit blocks
Basic Example: create a 5x5x5 hollow cube of stone and save to file:
```python
from nbt_structure_utils import NBTStructure, Vector, Cuboid, BlockData
nbtstructure = NBTStructure()
c1, c2 = Vector(0, 0, 0), Vector(4, 4, 4)
nbtstructure.fill_hollow(Cuboid(c1, c2), BlockData("stone"))
nbtstructure.get_nbt().write_file(filename="path/to/output/hollow_box.nbt")
```

### Read and Edit 
You can load and edit NBT structures created by this library or by Minecraft. All or part of a structure can also be cloned into other structures.

Example: Load from disk and mirror the structure to be upside down:
```python
from nbt_structure_utils import NBTStructure, Vector
nbtstructure = NBTStructure("path/to/existing_structure.nbt")
nbtstructure.reflect(Vector(None,0,None))
nbtstructure.get_nbt().write_file(filename="path/to/output/structure_flipped.nbt")
```

### Edit inventories
Create an Inventory and save it to desired blocks.
Example: Create a dropper with an enchanted wooden sword in the 5th slot:
```python
from nbt_structure_utils import NBTStructure, Vector, BlockData, Inventory, Enchantment
structure = NBTStructure()
inv_block_info = BlockData("dropper",[("facing","up")])
enchants = [Enchantment("sweeping", 3)]
inv = Inventory([ItemStack("wooden_sword", 1, 4, 0, enchants, None)])
structure.set_block(Vector(0, 0, 0), inv_block_info, inv, None)
nbtstructure.get_nbt().write_file(filename="path/to/output/sword_dropper.nbt")
```
