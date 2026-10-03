# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small, explicit 3-D operations used by the static KDL/RNE extraction.

No NumPy, Eigen, ROS, KDL binary, or hardware SDK is needed at runtime.
Rotations map vectors from child coordinates to parent coordinates.
"""

from math import cos, isfinite, sin, sqrt

Vector = tuple[float, float, float]
Matrix = tuple[Vector, Vector, Vector]
ZERO: Vector = (0.0, 0.0, 0.0)
IDENTITY: Matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def finite_vector(values, size=3):
    result = tuple(float(x) for x in values)
    if len(result) != size or not all(isfinite(x) for x in result):
        raise ValueError(f"expected {size} finite numbers")
    return result


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(factor * x for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def transpose(rotation):
    return tuple(zip(*rotation))


def rotate(rotation, vector):
    return tuple(dot(row, vector) for row in rotation)


def multiply(a, b):
    return tuple(tuple(dot(row, column) for column in transpose(b)) for row in a)


def normalize(axis):
    axis = finite_vector(axis)
    length = sqrt(dot(axis, axis))
    if not isfinite(length) or length == 0:
        raise ValueError("joint axis must have a finite nonzero norm")
    return scale(axis, 1.0 / length)


def axis_rotation(axis, angle):
    """Rodrigues formula; axis must already have unit length."""
    x, y, z = axis
    c, s = cos(angle), sin(angle)
    d = 1.0 - c
    return ((c+x*x*d, x*y*d-z*s, x*z*d+y*s),
            (y*x*d+z*s, c+y*y*d, y*z*d-x*s),
            (z*x*d-y*s, z*y*d+x*s, c+z*z*d))


def rpy_rotation(rpy):
    """URDF fixed-axis RPY: Rz(yaw) * Ry(pitch) * Rx(roll)."""
    roll, pitch, yaw = rpy
    return multiply(multiply(axis_rotation((0, 0, 1), yaw),
                             axis_rotation((0, 1, 0), pitch)),
                    axis_rotation((1, 0, 0), roll))
