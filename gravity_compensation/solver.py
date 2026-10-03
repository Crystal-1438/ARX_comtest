# SPDX-License-Identifier: LGPL-2.1-or-later
# Static specialization of Orocos KDL's recursive Newton-Euler algorithm.
# Original algorithm: Copyright (C) 2009 Ruben Smits and Dominick Vanthienen.
# Modified 2026-10-03: explicit Python vector math, zero velocity/acceleration,
# no external wrenches; ARX scaling kept separate from physical joint torque.
"""Offline ARX X5 gravity calculation, without importing the vendor SDK."""

from dataclasses import dataclass
from pathlib import Path

from .spatial import (IDENTITY, ZERO, add, cross, dot, finite_vector, multiply,
                      rotate, scale, transpose)
from .urdf import Segment, load_chain

SDK_SCALES = (0.8, 0.8, 0.8, 1.32, 1.32, 1.32)
MODEL_FILES = {"2023": "x5.urdf", "master": "x5_master.urdf", "2025": "x5_2025.urdf"}


@dataclass(frozen=True)
class GravityCompensator:
    segments: tuple[Segment, ...]
    gravity: tuple[float, float, float] = (0.0, 0.0, -9.81)

    def __post_init__(self):
        object.__setattr__(self, "gravity", finite_vector(self.gravity))

    @classmethod
    def from_urdf(cls, path, *, base="base_link", tip="link6", gravity=(0, 0, -9.81)):
        return cls(load_chain(path, base, tip), gravity)

    @classmethod
    def from_model(cls, model, *, gravity=(0, 0, -9.81)):
        """2023 -> SDK type 0; master -> type 1; 2025 -> type 2."""
        if model not in MODEL_FILES:
            raise ValueError(f"model must be one of {tuple(MODEL_FILES)}")
        return cls.from_urdf(Path(__file__).parent / "models" / MODEL_FILES[model], gravity=gravity)

    @property
    def joint_names(self):
        return tuple(s.joint_name for s in self.segments if s.movable)

    def _poses(self, q):
        q = iter(finite_vector(q, len(self.joint_names)))
        return tuple(s.pose(next(q) if s.movable else 0.0) for s in self.segments)

    def raw_torques(self, q):
        """Return holding torques G(q), before ARX's empirical scaling.

        q follows joint_names (rad for revolute, m for prismatic). Outputs
        are N*m for revolute and N for prismatic. They oppose gravity.
        This is KDL JntToGravity = RNE(q, qdot=0, qddot=0, f_ext=0).
        """
        poses = self._poses(q)
        forces, moments = [], []
        acceleration = scale(self.gravity, -1.0)  # KDL ag = -gravity
        # Forward sweep: express supporting acceleration in each link frame.
        for segment, (rotation, _) in zip(self.segments, poses):
            acceleration = rotate(transpose(rotation), acceleration)
            force = scale(acceleration, segment.mass)
            forces.append(force)
            moments.append(cross(segment.com, force))
        # Backward sweep: accumulate descendant wrench and project on axis.
        torques = []
        for i in range(len(self.segments) - 1, -1, -1):
            segment = self.segments[i]
            if segment.movable:
                wrench = forces[i] if segment.joint_type == "prismatic" else moments[i]
                torques.append(dot(segment.axis, wrench))
            if i:
                rotation, offset = poses[i]
                parent_force = rotate(rotation, forces[i])
                parent_moment = add(rotate(rotation, moments[i]), cross(offset, parent_force))
                forces[i-1] = add(forces[i-1], parent_force)
                moments[i-1] = add(moments[i-1], parent_moment)
        return tuple(reversed(torques))

    def sdk_torques(self, q):
        """Reproduce the six vendor gravity-command values, including scales.

        This is not CAN encoding, current conversion, or actuator limiting.
        Custom chains must preserve X5's six revolute joint names/order.
        """
        if self.joint_names != tuple(f"joint{i}" for i in range(1, 7)) or any(
            s.joint_type not in ("fixed", "revolute", "continuous") for s in self.segments
        ):
            raise ValueError("SDK scaling requires X5 joint1..joint6 in order")
        return tuple(t * s for t, s in zip(self.raw_torques(q), SDK_SCALES))

    def potential_energy(self, q):
        """U(q) = -sum(m * gravity dot world_COM), useful for independent checks."""
        rotation, position, energy = IDENTITY, ZERO, 0.0
        for segment, (local_rotation, offset) in zip(self.segments, self._poses(q)):
            position = add(position, rotate(rotation, offset))
            rotation = multiply(rotation, local_rotation)
            com = add(position, rotate(rotation, segment.com))
            energy -= segment.mass * dot(self.gravity, com)
        return energy
