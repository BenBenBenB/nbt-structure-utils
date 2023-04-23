import copy
from abc import ABC, abstractmethod
from collections.abc import Iterable
from math import floor

from nbt.nbt import TAG_Int, TAG_List


class Vector:
    """The 3D coordiantes of a position. Can create and read NBT.

    Methods:
        get_nbt(self, tag_name: str) -> TAG_List:
        copy(): Create a copy of self.
        add(__o): Add x, y, and z to self x, y, and z.
        sub(__o): Subtract x, y, and z to self x, y, and z.
        dot(__o): Calculate dot product of self and other vector.
        cross(__o): Calculate cross product of self and other vector.

    Static Methods:
        load_from_nbt(nbt): From NBT, load x, y, and z into a Vector
    """

    x: int
    y: int
    z: int
    __slots__ = ["x", "y", "z"]

    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __str__(self) -> str:
        return "(%d,%d,%d)" % (self.x, self.y, self.z)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

    def get_nbt(self, tag_name: str) -> TAG_List:
        """Create a new NBT Tag for the position.

        Args:
            tag_name (str): name to save for the new NBT tag.

        Returns:
            TAG_List: _description_
        """
        x, y, z = self.x, self.y, self.z
        # structures larger than 32x32x32 are allowed, just need to lie about the size
        if tag_name == "size":
            x = min([x, 32])
            y = min([y, 32])
            z = min([z, 32])

        nbt_pos = TAG_List(name=tag_name, type=TAG_Int)
        nbt_pos.tags.append(TAG_Int(x))
        nbt_pos.tags.append(TAG_Int(y))
        nbt_pos.tags.append(TAG_Int(z))
        return nbt_pos

    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y and self.z == __o.z

    def __add__(self, __o: object) -> "Vector":
        return Vector(self.x + __o.x, self.y + __o.y, self.z + __o.z)

    # Allow negatives for deltas
    def __sub__(self, __o: object) -> "Vector":
        return Vector(self.x - __o.x, self.y - __o.y, self.z - __o.z)

    def __mul__(self, __o: int) -> "Vector":
        if isinstance(__o, int):
            return Vector(self.x * __o, self.y * __o, self.z * __o)
        else:
            raise ValueError("Must multiply by scalar int.")

    def __floordiv__(self, __o: int) -> "Vector":
        return Vector(floor(self.x // __o), floor(self.y // __o), floor(self.z // __o))

    def copy(self) -> "Vector":
        """Create a copy of self."""
        return Vector(self.x, self.y, self.z)

    def add(self, __o: object) -> None:
        """Add x, y, and z to self."""
        self.x += __o.x
        self.y += __o.y
        self.z += __o.z

    def sub(self, __o: object) -> None:
        """Subtract x, y, and z from self."""
        self.x -= __o.x
        self.y -= __o.y
        self.z -= __o.z

    def dot(self, __o: "Vector") -> int:
        """Get the dot product of the two Vectors."""
        return self.x * __o.x + self.y * __o.y + self.z * __o.z

    def cross(self, __o: "Vector") -> "Vector":
        """Get the cross product of the two Vectors."""
        x = self.y * __o.z - self.z * __o.y
        y = self.z * __o.x - self.x * __o.z
        z = self.x * __o.y - self.y * __o.x
        return Vector(x, y, z)

    @staticmethod
    def load_from_nbt(nbt: TAG_List) -> "Vector":
        return Vector(nbt.tags[0].value, nbt.tags[1].value, nbt.tags[2].value)


class IVolume(ABC):
    """An interface from which geometric shapes and other custom volumes can be derived."""

    @abstractmethod
    def __iter__(self) -> "Iterable[Vector]":
        """Iterate over all coordinates within the volume."""
        raise NotImplementedError

    @abstractmethod
    def __next__(self) -> Vector:
        raise NotImplementedError

    @abstractmethod
    def contains(self, test_pos: Vector) -> bool:
        """Return true if the input vector is within the volume."""
        raise NotImplementedError

    @abstractmethod
    def exterior_contains(self, test_pos: Vector) -> bool:
        """Return true if the input coordinates are on any outside surface of the volume."""
        raise NotImplementedError

    @abstractmethod
    def interior_contains(self, test_pos: Vector) -> bool:
        """Return true if the input coordinates are within the volume but not on the exterior."""
        raise NotImplementedError

    @abstractmethod
    def edge_contains(self, test_pos: Vector) -> bool:
        """Return true if the input coordinates are on any edge of the volume."""
        raise NotImplementedError

    @abstractmethod
    def translate(self, delta: Vector) -> None:
        """Move the volume. Add delta vector to every point."""
        raise NotImplementedError

    def exterior(self) -> "Iterable[Vector]":
        """Get all coordinates along the outside surface of the volume."""
        return [pos.copy() for pos in iter(self) if self.exterior_contains(pos)]

    def interior(self) -> "Iterable[Vector]":
        """Get all coordinates within the volume that are completely surrounded."""
        return [pos.copy() for pos in iter(self) if self.interior_contains(pos)]

    def edge(self) -> "Iterable[Vector]":
        """Get all coordinates along the outside edges of the volume."""
        return [pos.copy() for pos in self if self.edge_contains(pos)]

    def would_clone_overlap(self, delta: Vector) -> bool:
        """If you took the whole volume and shifted it by delta, would any new positions overlap old ones?"""
        new_volume = self.copy()
        new_volume.translate(delta)
        return any(pos for pos in new_volume if self.contains(pos))

    def copy(self) -> "IVolume":
        return copy.deepcopy(self)


ADJACENCY_LIST = [
    Vector(1, 0, 0),
    Vector(-1, 0, 0),
    Vector(0, 1, 0),
    Vector(0, -1, 0),
    Vector(0, 0, 1),
    Vector(0, 0, -1),
]


class Volume(IVolume):
    """A custom volume with manually specified positions."""

    positions: "list[Vector]"

    def __init__(self, positions: "Iterable[Vector]") -> None:
        super().__init__()
        self.positions = [pos.copy() for pos in positions]

    def __iter__(self) -> "Iterable[Vector]":
        return iter(self.positions)

    def __next__(self) -> Vector:
        return self.positions.__next__()

    def __contains__(self, pos: Vector) -> bool:
        return self.contains(pos)

    def contains(self, test_pos: Vector) -> bool:
        return test_pos in self.positions

    def exterior_contains(self, test_pos: Vector) -> bool:
        if not self.contains(test_pos):
            return False
        return any(
            not self.contains(adj_pos)
            for adj_pos in [test_pos + adj for adj in ADJACENCY_LIST]
        )

    def interior_contains(self, test_pos: Vector) -> bool:
        if not self.contains(test_pos):
            return False
        return all(
            self.contains(adj_pos)
            for adj_pos in [test_pos + adj for adj in ADJACENCY_LIST]
        )

    def edge_contains(self, test_pos: Vector) -> bool:
        """For a generic volume, define block as edge if next to 2 or more empty spaces"""
        if not self.contains(test_pos):
            return False
        return [
            self.contains(adj_pos)
            for adj_pos in [test_pos + adj for adj in ADJACENCY_LIST]
        ].count(False) >= 2

    def translate(self, delta: Vector) -> None:
        for pos in self.positions:
            pos.add(delta)


class Cuboid(IVolume):
    """A 3D axis aligned box defined by blocks at two corners.

    Methods:
        copy: return copy of self
        size: return lengths of sides
        contains(coord): return true if coord is anywhere in or on cuboid
        exterior_contains(coord): return true if coord is on a face of the cuboid
        edge_contains(coord): return true if coord is on an edge of the cuboid
    """

    min_corner: Vector
    max_corner: Vector
    __iter_pos: Vector

    def __init__(self, coord1: Vector, coord2: Vector) -> None:
        super().__init__()
        self.min_corner, self.max_corner = Cuboid.__get_min_max_corners(coord1, coord2)

    def __iter__(self) -> "Iterable[Vector]":
        self.__iter_pos = self.min_corner.copy()
        self.__iter_pos.x -= 1
        return self

    def __next__(self) -> Vector:
        if self.__iter_pos.x < self.max_corner.x:
            self.__iter_pos.x += 1
            return self.__iter_pos
        if self.__iter_pos.y < self.max_corner.y:
            self.__iter_pos.x = self.min_corner.x
            self.__iter_pos.y += 1
            return self.__iter_pos
        if self.__iter_pos.z < self.max_corner.z:
            self.__iter_pos.x = self.min_corner.x
            self.__iter_pos.y = self.min_corner.y
            self.__iter_pos.z += 1
            return self.__iter_pos
        raise StopIteration

    def __len__(self) -> int:
        size = self.size()
        return size.x * size.y * size.z

    def copy(self) -> "Cuboid":
        return Cuboid(self.min_corner, self.max_corner)

    def size(self) -> Vector:
        return self.max_corner - self.min_corner + Vector(1, 1, 1)

    def translate(self, delta: Vector) -> None:
        self.min_corner += delta
        self.max_corner += delta

    def contains(self, test_pos: Vector) -> bool:
        return (
            self.min_corner.x <= test_pos.x <= self.max_corner.x
            and self.min_corner.y <= test_pos.y <= self.max_corner.y
            and self.min_corner.z <= test_pos.z <= self.max_corner.z
        )

    def exterior_contains(self, test_pos: Vector) -> bool:
        return self.contains(test_pos) and (
            (test_pos.x == self.min_corner.x or test_pos.x == self.max_corner.x)
            or (test_pos.y == self.min_corner.y or test_pos.y == self.max_corner.y)
            or (test_pos.z == self.min_corner.z or test_pos.z == self.max_corner.z)
        )

    def interior_contains(self, test_pos: Vector) -> bool:
        return (
            (self.min_corner.x < test_pos.x < self.max_corner.x)
            and (self.min_corner.y < test_pos.y < self.max_corner.y)
            and (self.min_corner.z < test_pos.z < self.max_corner.z)
        )

    def edge_contains(self, test_pos: Vector) -> bool:
        if not self.contains(test_pos):
            return False
        x_valid = test_pos.x == self.min_corner.x or test_pos.x == self.max_corner.x
        y_valid = test_pos.y == self.min_corner.y or test_pos.y == self.max_corner.y
        if x_valid and y_valid:
            return True
        z_valid = test_pos.z == self.min_corner.z or test_pos.z == self.max_corner.z
        return (x_valid and z_valid) or (y_valid and z_valid)

    def would_clone_overlap(self, delta: Vector) -> bool:
        min_pos = self.min_corner + Vector(1, 1, 1) - self.size()
        max_pos = self.max_corner
        return Cuboid(min_pos, max_pos).contains(delta)

    @staticmethod
    def __get_min_max_corners(c1: "Vector", c2: "Vector") -> "Vector":
        min_coord = Vector(min([c1.x, c2.x]), min([c1.y, c2.y]), min([c1.z, c2.z]))
        max_coord = Vector(max([c1.x, c2.x]), max([c1.y, c2.y]), max([c1.z, c2.z]))
        return min_coord, max_coord


# lines can be straight or curved.
class LineSegment:
    points: "list[Vector]"

    def __init__(self, points: "list[Vector]") -> None:
        self.points = points

    def draw_straight_lines(self) -> "Iterable[Vector]":
        """Draw a straight line 1 block wide from each point to the next in the list, like connect the dots.

        Raises:
            ValueError: Must have at least two points in list

        Returns:
            list[Vector]: A list of all points to be drawn for the line(s).
        """
        points_on_lines = []
        if len(self.points) < 2:
            raise ValueError("Need at least two points.")
        for i in range(len(self.points) - 1):
            new_line = self.__bresenham(i)
            points_on_lines.extend(filter(lambda pos: pos not in self.points, new_line))
        return points_on_lines

    # adapted from https://www.geeksforgeeks.org/bresenhams-algorithm-for-3-d-line-drawing/
    def __bresenham(self, i) -> "list[Vector]":  # noqa: C901
        """Draw a straight 1 block wide line between two points.

        Returns:
            list[Vector]: A list of all points to be drawn for the line.
        """
        pointA = self.points[i].copy()
        pointB = self.points[i + 1].copy()
        points_on_line = []
        points_on_line.append(pointA.copy())
        dx = abs(pointB.x - pointA.x)
        dy = abs(pointB.y - pointA.y)
        dz = abs(pointB.z - pointA.z)

        xs = 1 if pointB.x > pointA.x else -1
        ys = 1 if pointB.y > pointA.y else -1
        zs = 1 if pointB.z > pointA.z else -1

        # Driving axis is X-axis"
        if dx >= dy and dx >= dz:
            p1 = 2 * dy - dx
            p2 = 2 * dz - dx
            while pointA.x != pointB.x:
                pointA.x += xs
                if p1 >= 0:
                    pointA.y += ys
                    p1 -= 2 * dx
                if p2 >= 0:
                    pointA.z += zs
                    p2 -= 2 * dx
                p1 += 2 * dy
                p2 += 2 * dz
                points_on_line.append(pointA.copy())

        # Driving axis is Y-axis"
        elif dy >= dx and dy >= dz:
            p1 = 2 * dx - dy
            p2 = 2 * dz - dy
            while pointA.y != pointB.y:
                pointA.y += ys
                if p1 >= 0:
                    pointA.x += xs
                    p1 -= 2 * dy
                if p2 >= 0:
                    pointA.z += zs
                    p2 -= 2 * dy
                p1 += 2 * dx
                p2 += 2 * dz
                points_on_line.append(pointA.copy())

        # Driving axis is Z-axis"
        else:
            p1 = 2 * dy - dz
            p2 = 2 * dx - dz
            while pointA.z != pointB.z:
                pointA.z += zs
                if p1 >= 0:
                    pointA.y += ys
                    p1 -= 2 * dz
                if p2 >= 0:
                    pointA.x += xs
                    p2 -= 2 * dz
                p1 += 2 * dy
                p2 += 2 * dx
                points_on_line.append(pointA.copy())
        return points_on_line
