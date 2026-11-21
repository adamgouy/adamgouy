"""Operator overloading exercises.

Statement: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc (slide 67)

Python translates an operator into a call to a "dunder" (double underscore) method:
`a + b` calls `a.__add__(b)`, `a > b` calls `a.__gt__(b)`, and so on. Defining these
methods in a class makes the operators work on its objects.
"""
from __future__ import annotations

import math
from functools import total_ordering


# --- Complex numbers: + and - -------------------------------------------------

class Complex:
    def __init__(self, real: float, imaginary: float):
        self.real = real
        self.imaginary = imaginary

    def __add__(self, other: Complex) -> Complex:
        return Complex(self.real + other.real, self.imaginary + other.imaginary)

    def __sub__(self, other: Complex) -> Complex:
        return Complex(self.real - other.real, self.imaginary - other.imaginary)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Complex):
            return NotImplemented   # lets Python try other.__eq__ instead of answering False
        return (self.real, self.imaginary) == (other.real, other.imaginary)

    def __str__(self) -> str:
        sign = "-" if self.imaginary < 0 else "+"
        return f"{self.real} {sign} {abs(self.imaginary)}i"

    def __repr__(self) -> str:
        return f"Complex({self.real}, {self.imaginary})"


# --- Person: compare two persons by age with > --------------------------------

class Person:
    def __init__(self, name: str, age: int, gender: str):
        self.name = name
        self.age = age
        self.gender = gender

    def __gt__(self, other: Person) -> bool:
        return self.age > other.age

    def __repr__(self) -> str:
        return f"Person({self.name!r}, age={self.age})"


# --- Vector: * is the dot product ----------------------------------------------

class Vector:
    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    def __mul__(self, other: Vector) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y}, {self.z})"


# --- Circle: the 6 comparison operators, written one by one --------------------

class Circle:
    def __init__(self, radius: float):
        if radius < 0:
            raise ValueError("A radius cannot be negative")
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            return NotImplemented
        return self.radius == other.radius

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            return NotImplemented
        return self.radius != other.radius

    def __lt__(self, other: Circle) -> bool:
        return self.radius < other.radius

    def __le__(self, other: Circle) -> bool:
        return self.radius <= other.radius

    def __gt__(self, other: Circle) -> bool:
        return self.radius > other.radius

    def __ge__(self, other: Circle) -> bool:
        return self.radius >= other.radius

    def __repr__(self) -> str:
        return f"Circle(r={self.radius})"


# --- Point: compared by distance to the origin --------------------------------
# Writing 6 methods like in Circle is repetitive: @total_ordering only needs
# __eq__ and one of __lt__/__le__/__gt__/__ge__ and generates the others.

@total_ordering
class Point:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    def distance_to_origin(self) -> float:
        return math.hypot(self.x, self.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return math.isclose(self.distance_to_origin(), other.distance_to_origin())

    def __lt__(self, other: Point) -> bool:
        return self.distance_to_origin() < other.distance_to_origin()

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


# --- Matrix: * is the matrix product ------------------------------------------

class Matrix:
    def __init__(self, rows: list[list[float]]):
        if not rows or not rows[0] or len({len(row) for row in rows}) != 1:
            raise ValueError("A matrix needs at least one row and rows of the same length")
        self.rows = [list(row) for row in rows]

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return len(self.rows[0])

    def column(self, j: int) -> list[float]:
        return [row[j] for row in self.rows]

    def __mul__(self, other: Matrix) -> Matrix:
        # (n x m) * (m x p) = (n x p): the inner dimensions must match
        if self.n_cols != other.n_rows:
            raise ValueError(
                f"Cannot multiply a {self.n_rows}x{self.n_cols} matrix "
                f"by a {other.n_rows}x{other.n_cols} matrix"
            )
        return Matrix([
            [sum(a * b for a, b in zip(row, other.column(j))) for j in range(other.n_cols)]
            for row in self.rows
        ])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.rows == other.rows

    def __str__(self) -> str:
        return "\n".join("  ".join(f"{value:>5}" for value in row) for row in self.rows)

    def __repr__(self) -> str:
        return f"Matrix({self.rows})"


if __name__ == "__main__":
    print("Complex:", Complex(2, 3) + Complex(1, -4), "|", Complex(2, 3) - Complex(1, -4))

    sara, tom = Person("Sara", 28, "F"), Person("Tom", 34, "M")
    print("Is Sara older than Tom?", sara > tom)

    print("Dot product:", Vector(1, 0, 2) * Vector(3, 5, 4))

    small, big = Circle(1.5), Circle(4)
    print("Circles:", small < big, small == Circle(1.5), big >= small, small != big)

    print("Points:", Point(3, 4) == Point(5, 0), Point(1, 1) < Point(3, 4))
    print("Sorted points:", sorted([Point(6, 8), Point(0, 1), Point(3, 4)]))

    a = Matrix([[1, 2, 3], [4, 5, 6]])
    b = Matrix([[7, 8], [9, 10], [11, 12]])
    print("Matrix product:")
    print(a * b)
