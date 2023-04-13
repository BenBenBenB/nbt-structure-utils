# NBTStructureUtils

> A python library to create and edit NBT structure files for Minecraft.

**Features**

- Create, read, and edit NBT structure files.
- Methods inspired by Minecraft's fill, setblock, and clone commands.
- Edit the inventory of any block.
- Update blocks within cuboids.
- Draw lines of blocks to connect coordinates.

## Basic Usage

### Edit blocks
Example: create a 5x5x5 hollow cube of stone:
```python
from nbt_structure_utils.NBTStructure import NBTStructure
from nbt_structure_utils.plot_helpers import Vector
from nbt_structure_utils.blocks import BlockData
nbtstructure = NBTStructure()
c1, c2 = Vector(0, 0, 0), Vector(4, 4, 4)
nbtstructure.fill_hollow(Cuboid(c1, c2), BlockData("stone"))
nbtstructure.get_nbt().write_file(filename="./output/test.nbt")
```
