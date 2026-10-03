# SPDX-License-Identifier: LGPL-2.1-or-later
"""Extract the URDF quantities needed for static gravity compensation.

Equivalent geometry conventions to kdl_parser::toKdl / addChildrenToTree.
Inertial RPY and rotational inertia are deliberately unnecessary at rest:
only link mass and link-frame COM enter the gravity wrench.
"""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET

from .spatial import (Matrix, Vector, ZERO, add, axis_rotation, finite_vector,
                      multiply, normalize, rotate, rpy_rotation, scale)


@dataclass(frozen=True)
class Segment:
    joint_name: str
    link_name: str
    joint_type: str
    xyz: Vector
    rpy: Vector
    rotation: Matrix
    axis: Vector
    mass: float
    com: Vector

    @property
    def movable(self):
        return self.joint_type != "fixed"

    def pose(self, q):
        if self.joint_type in ("revolute", "continuous"):
            return multiply(self.rotation, axis_rotation(self.axis, q)), self.xyz
        if self.joint_type == "prismatic":
            return self.rotation, add(self.xyz, rotate(self.rotation, scale(self.axis, q)))
        return self.rotation, self.xyz


def _vector(element, attribute, default="0 0 0"):
    value = default if element is None else element.get(attribute, default)
    return finite_vector(value.split())


def load_chain(path: str | Path, base="base_link", tip="link6"):
    """Read one ancestor-to-descendant chain, including its fixed segments.

    Sibling branches, the base's own inertia, meshes and joint limits do not
    contribute to KDL's selected chain. Mimic/unsupported joints are rejected
    rather than silently given an incorrect independent coordinate.
    """
    root = ET.parse(path).getroot()
    if root.tag != "robot":
        raise ValueError("expected a URDF <robot> element")
    links = {}
    for link in root.findall("link"):
        name = link.get("name")
        if not name or name in links:
            raise ValueError("missing or duplicate link name")
        links[name] = link
    if base not in links or tip not in links or base == tip:
        raise ValueError("base and tip must be distinct existing links")
    parents, joint_names = {}, set()
    for joint in root.findall("joint"):
        name = joint.get("name")
        parent, child = joint.find("parent"), joint.find("child")
        if not name or name in joint_names or parent is None or child is None:
            raise ValueError("invalid or duplicate joint")
        joint_names.add(name)
        parent_name, child_name = parent.get("link"), child.get("link")
        if parent_name not in links or child_name not in links or child_name in parents:
            raise ValueError("invalid joint links or multiple parents")
        parents[child_name] = (parent_name, joint)
    selected, visited = [], set()
    current = tip
    while current != base:
        if current in visited or current not in parents:
            raise ValueError(f"no acyclic chain from {base!r} to {tip!r}")
        visited.add(current)
        parent, joint = parents[current]
        kind = joint.get("type")
        if kind not in ("fixed", "revolute", "continuous", "prismatic"):
            raise ValueError(f"unsupported joint type: {kind}")
        if joint.find("mimic") is not None:
            raise ValueError("mimic joints require an explicit coordinate mapping")
        origin = joint.find("origin")
        xyz, rpy = _vector(origin, "xyz"), _vector(origin, "rpy")
        axis = ZERO if kind == "fixed" else normalize(_vector(joint.find("axis"), "xyz", "1 0 0"))
        inertial = links[current].find("inertial")
        mass, com = 0.0, ZERO
        if inertial is not None:
            mass_element = inertial.find("mass")
            if mass_element is None:
                raise ValueError(f"missing inertial mass in {current}")
            mass = float(mass_element.attrib["value"])
            if not isfinite(mass) or mass < 0:
                raise ValueError("link mass must be finite and nonnegative")
            com = _vector(inertial.find("origin"), "xyz")
        selected.append(Segment(joint.get("name"), current, kind, xyz, rpy,
                                rpy_rotation(rpy), axis, mass, com))
        current = parent
    return tuple(reversed(selected))
