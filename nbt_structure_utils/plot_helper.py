from math import floor

from nbt.nbt import TAG_Int, TAG_List


class Vector:
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
            raise ValueError("Must multiply by scalar int")

    def __floordiv__(self, __o: int) -> "Vector":
        return Vector(floor(self.x // __o), floor(self.y // __o), floor(self.z // __o))

    def copy(self) -> "Vector":
        return Vector(self.x, self.y, self.z)

    def add(self, __o: object) -> None:
        """add x,y,z to self"""
        self.x += __o.x
        self.y += __o.y
        self.z += __o.z

    def sub(self, __o: object) -> None:
        """subtract x,y,z from self"""
        self.x -= __o.x
        self.y -= __o.y
        self.z -= __o.z

    def dot(self, __o: "Vector") -> int:
        """Get the dot product of the two Vectors"""
        return self.x * __o.x + self.y * __o.y + self.z * __o.z

    def cross(self, __o: "Vector") -> "Vector":
        """Get the cross product of the two Vectors"""
        x = self.y * __o.z - self.z * __o.y
        y = self.z * __o.x - self.x * __o.z
        z = self.x * __o.y - self.y * __o.x
        return Vector(x, y, z)

    @staticmethod
    def load_from_nbt(nbt: TAG_List) -> "Vector":
        return Vector(nbt.tags[0].value, nbt.tags[1].value, nbt.tags[2].value)


class Cuboid:
    """A 3D axis aligned box defined by blocks at two corners.
    You can iterate through all Coordinates contained in the corners.

    Methods:
        copy: return copy of self
        size: return lengths of sides
        contains(coord): return true if coord is anywhere in or on cuboid
        boundary_contains(coord): return true if coord is on a face of the cuboid
        edge_contains(coord): return true if coord is on an edge of the cuboid
    """

    min_corner: Vector
    max_corner: Vector

    __iter_pos: Vector

    def __init__(self, coord1: Vector, coord2: Vector) -> None:
        self.min_corner, self.max_corner = Cuboid.__get_min_max_corners(coord1, coord2)

    def __iter__(self) -> "Cuboid":
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

    def contains(self, coord: Vector) -> bool:
        return (
            self.min_corner.x <= coord.x <= self.max_corner.x
            and self.min_corner.y <= coord.y <= self.max_corner.y
            and self.min_corner.z <= coord.z <= self.max_corner.z
        )

    def boundary_contains(self, coord: Vector) -> bool:
        return self.contains(coord) and (
            (coord.x == self.min_corner.x or coord.x == self.max_corner.x)
            or (coord.y == self.min_corner.y or coord.y == self.max_corner.y)
            or (coord.z == self.min_corner.z or coord.z == self.max_corner.z)
        )

    def edge_contains(self, coord: Vector) -> bool:
        if not self.contains(coord):
            return False
        x_valid = coord.x == self.min_corner.x or coord.x == self.max_corner.x
        y_valid = coord.y == self.min_corner.y or coord.y == self.max_corner.y
        if x_valid and y_valid:
            return True
        z_valid = coord.z == self.min_corner.z or coord.z == self.max_corner.z
        return (x_valid and z_valid) or (y_valid and z_valid)

    @staticmethod
    def __get_min_max_corners(coord1: "Vector", coord2: "Vector") -> "Vector":
        min_coord = Vector(
            min([coord1.x, coord2.x]),
            min([coord1.y, coord2.y]),
            min([coord1.z, coord2.z]),
        )
        max_coord = Vector(
            max([coord1.x, coord2.x]),
            max([coord1.y, coord2.y]),
            max([coord1.z, coord2.z]),
        )
        return min_coord, max_coord


# lines can be straight or curved.
class LineSegment:
    points: "list[Vector]"

    def __init__(self, points: "list[Vector]") -> None:
        self.points = points

    def draw_straight_lines(self) -> "list[Vector]":
        """Draw a straight 1 block wide from each point to the next in the list, like connect the dots.

        Raises:
            ValueError: Must have at least two points in list

        Returns:
            list[Vector]: A list of all points to be drawn for the line(s).
        """
        points_on_line = []
        if len(self.points) < 2:
            raise ValueError("Need at least two points.")
        for i in range(len(self.points) - 1):
            points_on_line.extend(self.__bresenham3D(i))
        return list(set(points_on_line))

    # adapted from https://www.geeksforgeeks.org/bresenhams-algorithm-for-3-d-line-drawing/
    def __bresenham3D(self, i) -> "list[Vector]":  # noqa: C901, N802
        """Draw a straight 1 block wide line between two points.

        Returns:
            list[Vector]: A list of all points to be drawn for the line.
        """
        pointA = self.points[i].copy()
        pointB = self.points[i + 1].copy()
        ListOfPoints = []
        ListOfPoints.append(pointA.copy())
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
                ListOfPoints.append(pointA.copy())

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
                ListOfPoints.append(pointA.copy())

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
                ListOfPoints.append(pointA.copy())
        return ListOfPoints
