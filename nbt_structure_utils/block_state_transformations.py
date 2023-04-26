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

ROTATE_PROPS_X_90 = [
    ("up", "south"),
    ("south", "down"),
    ("down", "north"),
    ("north", "up"),
    ("ascending_north", "ascending_south"),
    ("ascending_south", "ascending_north"),
    ("y", "z"),
    ("z", "y"),
]
ROTATE_PROPS_Y_90 = [
    ("north", "west"),
    ("west", "south"),
    ("south", "east"),
    ("east", "north"),
    ("north_east", "north_west"),
    ("north_west", "south_west"),
    ("south_west", "south_east"),
    ("south_east", "north_east"),
    ("ascending_north", "ascending_west"),
    ("ascending_west", "ascending_south"),
    ("ascending_south", "ascending_east"),
    ("ascending_east", "ascending_north"),
    ("x", "z"),
    ("z", "x"),
]
ROTATE_PROPS_Z_90 = [
    ("up", "west"),
    ("west", "down"),
    ("down", "east"),
    ("east", "up"),
    ("ascending_west", "ascending_east"),
    ("ascending_east", "ascending_west"),
    ("x", "y"),
    ("y", "x"),
]

BLOCK_SUFFIXES_ROTATION_ALLOW = ["_head", "_skull", "_sign", "_banner"]
BLOCK_SUFFIXES_ROTATION_FORBID = [
    "_wall" + suffix for suffix in BLOCK_SUFFIXES_ROTATION_ALLOW
]

BLOCK_SUFFIXES_FACE_ALLOW = ["_button", "lever", "grindstone"]
