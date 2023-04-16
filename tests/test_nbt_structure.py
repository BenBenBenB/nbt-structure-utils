import pytest

from nbt_structure_utils.blocks import BlockData
from nbt_structure_utils.items import Enchantment, ItemStack
from nbt_structure_utils.nbt_structure import AIR_BLOCK, NBTStructure
from nbt_structure_utils.shapes import Cuboid, LineSegment, Vector

coordinate_groups = [
    [Vector(0, 0, 0), Vector(3, 4, 5), Vector(1, 1, 1), Vector(2, 2, 2)],
    [Vector(-5, -2, 2), Vector(-6, -1, 4), Vector(-6, 1, 0), Vector(-6, 0, 5)],
    [Vector(1, -2, 3), Vector(9, -21, 29), Vector(2, -3, 4), Vector(10, -22, 30)],
]

test_coords = ((coord[0]) for coord in coordinate_groups)
test_coord_pairs = ((coord[0], coord[1]) for coord in coordinate_groups)
test_volumes = [(Cuboid(coords[0], coords[1])) for coords in coordinate_groups]
test_volume_pairs = [
    (Cuboid(coords[0], coords[1]), Cuboid(coords[1], coords[2]))
    for coords in coordinate_groups
]
test_volume_vector = [
    (Cuboid(coords[0], coords[1]), coords[2]) for coords in coordinate_groups
]
test_line_segments = [
    (LineSegment([coords[0], coords[1], coords[2], coords[3]]))
    for coords in coordinate_groups
]


@pytest.fixture
def nbtstructure() -> NBTStructure:
    return NBTStructure()


@pytest.fixture
def nbtstructure_from_file() -> NBTStructure:
    return NBTStructure("tests/nbt_files/test_structure.nbt")


@pytest.fixture
def block1() -> BlockData:
    return BlockData("dirt")


@pytest.fixture
def block2() -> BlockData:
    return BlockData("stone")


def has_no_blocks_outside_volume(structure: NBTStructure, cuboid_vol: Cuboid) -> bool:
    return not any(not cuboid_vol.contains(b.pos) for b in structure.blocks.values())


def test_new_structure(nbtstructure: NBTStructure) -> None:
    assert not nbtstructure.blocks
    assert not any(nbtstructure.palette)


def test_load_file(nbtstructure_from_file: NBTStructure) -> None:
    block = nbtstructure_from_file.get_block_state(Vector(0, 0, 0))
    inventory = nbtstructure_from_file.get_block_inventory(Vector(0, 0, 0))
    assert block == BlockData("red_concrete")
    assert inventory is None

    block = nbtstructure_from_file.get_block_state(Vector(0, 1, 0))
    inventory = nbtstructure_from_file.get_block_inventory(Vector(0, 1, 0))
    assert block == BlockData("redstone_torch", [("lit", "true")])
    assert inventory is None

    block = nbtstructure_from_file.get_block_state(Vector(0, 2, 0))
    inventory = nbtstructure_from_file.get_block_inventory(Vector(0, 2, 0))
    assert block == BlockData("dropper", [("facing", "down"), ("triggered", "true")])
    assert inventory.container_name == "minecraft:dropper"
    assert len(inventory.items) == 1
    assert next(iter(inventory.items)) == ItemStack(
        item_id="minecraft:wooden_sword",
        count=1,
        slot=4,
        damage=0,
        enchantments=[Enchantment("minecraft:sharpness", 4)],
    )

    block = nbtstructure_from_file.get_block_state(Vector(0, 3, 0))
    inventory = nbtstructure_from_file.get_block_inventory(Vector(0, 3, 0))
    assert block == AIR_BLOCK
    assert inventory is None


def test_set_block(nbtstructure: NBTStructure, block1: BlockData) -> None:
    nbtstructure.set_block(Vector(0, 0, 0), block1)
    block = nbtstructure.get_block_state(Vector(0, 0, 0))
    assert block == block1
    assert len(nbtstructure.blocks) == 1

    nbtstructure.set_block(Vector(0, 0, 0), None)
    block = nbtstructure.get_block_state(Vector(0, 0, 0))
    assert block is None
    assert not nbtstructure.blocks


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_fill_cuboid(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, block1: BlockData
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert all(nbtstructure.get_block_state(pos) == block1 for pos in cuboid_vol)


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_fill_hollow_cuboid(
    nbtstructure: NBTStructure,
    cuboid_vol: Cuboid,
    block1: BlockData,
    block2: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure.fill_hollow(cuboid_vol, block2)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert all(nbtstructure.get_block_state(pos) != block1 for pos in cuboid_vol)
    assert all(
        nbtstructure.get_block_state(pos) == AIR_BLOCK
        for pos in cuboid_vol
        if not cuboid_vol.exterior_contains(pos)
    )
    assert all(
        nbtstructure.get_block_state(pos) == block2
        for pos in cuboid_vol
        if cuboid_vol.exterior_contains(pos)
    )


@pytest.mark.parametrize("cuboid_vol_1,cuboid_vol_2", test_volume_pairs)
def test_fill_keep(
    nbtstructure: NBTStructure,
    cuboid_vol_1: Cuboid,
    cuboid_vol_2: Cuboid,
    block1: BlockData,
    block2: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol_1, block1)
    nbtstructure.fill_keep(cuboid_vol_1, block2)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol_1)
    assert all(nbtstructure.get_block_state(pos) == block1 for pos in cuboid_vol_1)

    nbtstructure.fill_keep(cuboid_vol_2, block2)


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_fill_outline_cuboid(
    nbtstructure: NBTStructure,
    cuboid_vol: Cuboid,
    block1: BlockData,
    block2: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure.fill(cuboid_vol.exterior(), block2)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert all(
        nbtstructure.get_block_state(pos) == block2
        for pos in cuboid_vol
        if cuboid_vol.exterior_contains(pos)
    )
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in cuboid_vol
        if not cuboid_vol.exterior_contains(pos)
    )


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_fill_frame(
    nbtstructure: NBTStructure,
    cuboid_vol: Cuboid,
    block1: BlockData,
    block2: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure.fill(cuboid_vol.edge(), block2)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert all(
        nbtstructure.get_block_state(pos) == block2
        for pos in cuboid_vol
        if cuboid_vol.edge_contains(pos)
    )
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in cuboid_vol
        if not cuboid_vol.edge_contains(pos)
    )


@pytest.mark.parametrize("cuboid_vol_1,cuboid_vol_2", test_volume_pairs)
def test_fill_replace(
    nbtstructure: NBTStructure,
    cuboid_vol_1: Cuboid,
    cuboid_vol_2: Cuboid,
    block1: BlockData,
    block2: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol_1, block1)
    nbtstructure.fill_replace(cuboid_vol_2, block1, block2)
    assert nbtstructure.palette.try_get_state(block2) is None

    nbtstructure.fill_replace(cuboid_vol_2, block2, block1)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol_1)
    assert all(
        nbtstructure.get_block_state(pos) == block2
        for pos in cuboid_vol_2
        if cuboid_vol_1.contains(pos)
    )
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in cuboid_vol_1
        if not cuboid_vol_2.contains(pos)
    )


@pytest.mark.parametrize("coord1,coord2", (test_coord_pairs))
def test_clone_block(
    nbtstructure: NBTStructure, coord1: Vector, coord2: Vector, block1: BlockData
) -> None:
    nbtstructure.set_block(coord1, block1)
    nbtstructure.clone_block(coord1, coord2)
    if coord1 == coord2:
        assert len(nbtstructure.blocks) == 1
    else:
        assert len(nbtstructure.blocks) == 2
    assert nbtstructure.get_block_state(coord2) == block1

    nbtstructure.set_block(coord1, None)
    nbtstructure.clone_block(coord1, coord2)
    if coord1 == coord2:
        assert len(nbtstructure.blocks) == 0
    else:
        assert len(nbtstructure.blocks) == 1
    assert nbtstructure.get_block_state(coord2) == block1


@pytest.mark.parametrize("cuboid_vol,dest", test_volume_vector)
def test_clone(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, dest: Vector, block1: BlockData
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    start_size = len(nbtstructure.blocks)
    delta = dest - cuboid_vol.min_corner
    try:
        nbtstructure.clone(cuboid_vol, dest)
        assert len(nbtstructure.blocks) == 2 * start_size
        assert all(
            nbtstructure.get_block_state(pos)
            == nbtstructure.get_block_state(pos + delta)
            for pos in cuboid_vol
        )
    except ValueError:
        assert start_size == len(nbtstructure.blocks)


@pytest.mark.parametrize("cuboid_vol,dest", test_volume_vector)
def test_clone_structure(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, dest: Vector, block1: BlockData
) -> None:
    nbtstructure2 = NBTStructure()
    nbtstructure2.clone_structure(nbtstructure, dest)
    assert not any(nbtstructure.blocks) and not any(nbtstructure2.blocks)

    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure2.clone_structure(nbtstructure, dest)
    assert len(nbtstructure.blocks) == len(nbtstructure2.blocks)
    assert all(
        nbtstructure.get_block_state(pos) == nbtstructure2.get_block_state(pos + dest)
        for pos in cuboid_vol
    )


@pytest.mark.parametrize("cuboid_vol,delta", test_volume_vector)
def test_translate(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, delta: Vector, block1: BlockData
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure.translate(delta)
    new_volume = cuboid_vol.copy()
    new_volume.translate(delta)
    assert has_no_blocks_outside_volume(nbtstructure, new_volume)
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in new_volume
        if cuboid_vol.contains(pos)
    )


@pytest.mark.parametrize("cuboid_vol_1,cuboid_vol_2", test_volume_pairs)
def test_crop(
    nbtstructure: NBTStructure,
    cuboid_vol_1: Cuboid,
    cuboid_vol_2: Cuboid,
    block1: BlockData,
) -> None:
    nbtstructure.fill(cuboid_vol_1, block1)
    nbtstructure.crop(cuboid_vol_2)
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol_2)
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in cuboid_vol_1
        if cuboid_vol_2.contains(pos)
    )


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_pressurize(nbtstructure: NBTStructure, cuboid_vol: Cuboid) -> None:
    nbtstructure.set_block(cuboid_vol.min_corner, AIR_BLOCK)
    nbtstructure.set_block(cuboid_vol.max_corner, AIR_BLOCK)
    assert len(nbtstructure.blocks) == 2
    nbtstructure.pressurize()
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert len(nbtstructure.blocks) == len(cuboid_vol)
    assert all(nbtstructure.get_block_state(pos) == AIR_BLOCK for pos in cuboid_vol)


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_depressurize(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, block1: BlockData
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtstructure.set_block(cuboid_vol.max_corner, AIR_BLOCK)
    nbtstructure.depressurize()
    assert has_no_blocks_outside_volume(nbtstructure, cuboid_vol)
    assert nbtstructure.get_block_state(cuboid_vol.max_corner) is None
    assert all(
        nbtstructure.get_block_state(pos) == block1
        for pos in cuboid_vol
        if pos != cuboid_vol.max_corner
    )


@pytest.mark.parametrize("cuboid_vol", test_volumes)
def test_get_nbt(
    nbtstructure: NBTStructure, cuboid_vol: Cuboid, block1: BlockData
) -> None:
    nbtstructure.fill(cuboid_vol, block1)
    nbtfile = nbtstructure.get_nbt()

    assert len(nbtstructure.blocks) == len(cuboid_vol)
    assert nbtstructure.get_min_coords() == cuboid_vol.min_corner
    assert nbtstructure.get_max_coords() == cuboid_vol.max_corner

    max_length = 32
    size = nbtstructure.size()
    nbt_size = [t.value for t in nbtfile["size"].tags]

    assert len(nbtfile["size"].tags) == 3
    assert max_length == nbt_size[0] if size.x > max_length else size.x == nbt_size[0]
    assert max_length == nbt_size[1] if size.y > max_length else size.y == nbt_size[1]
    assert max_length == nbt_size[2] if size.z > max_length else size.z == nbt_size[2]

    assert len(nbtfile["blocks"].tags) == len(cuboid_vol)
    assert all(block["state"].value == 0 for block in nbtfile["blocks"].tags)

    assert len(nbtfile["palette"].tags) == 1
    assert nbtfile["palette"].tags[0]["Name"].value == block1.name
