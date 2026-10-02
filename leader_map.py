"""Leader single-turn encoder angles to vendor joint radians.

The leader board reports absolute single-turn angles, so it carries no zero
reference of its own. Turning them into vendor joint coordinates needs three
per-joint facts that no amount of parsing can recover: the rotation direction,
which leader angle corresponds to the vendor's zero, and whether the joint
travels more than one full turn.

Those live in a calibration file. Until it is filled in and marked
``"calibrated": true`` the mapper still runs, but only as an identity-ish
placeholder -- see ``LeaderMap.calibrated`` and the gate in ``app.py``.
"""

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path

DEFAULT_MAP_NAME = "leader_map.json"
ENV_VAR = "ARX_LEADER_MAP"
JOINTS = 6
FIELDS = ("sign", "offset_deg", "unwrap")


@dataclass(frozen=True)
class JointMap:
    """``sdk_deg = sign * continuous_deg + offset_deg`` for one joint."""

    sign: float = 1.0
    offset_deg: float = 0.0
    unwrap: bool = True


@dataclass(frozen=True)
class LeaderMap:
    joints: tuple
    calibrated: bool = False
    source: str = "<uncalibrated default>"


def uncalibrated():
    """Placeholder used when no calibration file exists yet.

    Angles pass through with only the 0.1 degree scaling, which is enough to
    watch a live stream but is not a valid teleoperation mapping.
    """
    return LeaderMap(joints=(JointMap(),) * JOINTS)


def resolve_mapping_path(decoder_path=None, explicit=None, environ=None):
    """Single authority for where calibration comes from.

    ``app.py`` uses this too, so the file the startup gate approves is always
    the file the decoder actually loads.
    """
    environ = os.environ if environ is None else environ
    if explicit:
        return Path(explicit)
    override = environ.get(ENV_VAR)
    if override:
        return Path(override)
    base = Path(decoder_path).resolve().parent if decoder_path else Path(__file__).resolve().parent
    return base / DEFAULT_MAP_NAME


def _number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _joint(entry, index):
    if not isinstance(entry, dict):
        raise ValueError(f"joints[{index}] must be an object")
    unknown = set(entry) - set(FIELDS)
    if unknown:
        raise ValueError(f"joints[{index}] has unknown fields: {sorted(unknown)}")
    sign = _number(entry.get("sign", 1.0), f"joints[{index}].sign")
    if sign not in (-1.0, 1.0):
        raise ValueError(f"joints[{index}].sign must be 1 or -1")
    unwrap = entry.get("unwrap", True)
    if type(unwrap) is not bool:
        raise ValueError(f"joints[{index}].unwrap must be boolean")
    return JointMap(sign, _number(entry.get("offset_deg", 0.0), f"joints[{index}].offset_deg"),
                    unwrap)


def load_mapping(path):
    """Load calibration, or return the uncalibrated placeholder if absent.

    A file that exists but is wrong is an error: a typo in a sign or offset
    silently teleoperating the arm in the wrong direction is worse than not
    starting.
    """
    path = Path(path)
    if not path.is_file():
        return uncalibrated()
    with open(path, encoding="utf-8") as stream:
        config = json.load(stream)
    if not isinstance(config, dict):
        raise ValueError("leader map must be a JSON object")
    unknown = set(config) - {"calibrated", "joints", "comment"}
    if unknown:
        raise ValueError(f"leader map has unknown fields: {sorted(unknown)}")
    calibrated = config.get("calibrated", False)
    if type(calibrated) is not bool:
        raise ValueError("calibrated must be boolean")
    joints = config.get("joints")
    if not isinstance(joints, list) or len(joints) != JOINTS:
        raise ValueError(f"leader map needs exactly {JOINTS} joints")
    return LeaderMap(tuple(_joint(entry, i) for i, entry in enumerate(joints)),
                     calibrated, str(path))


class Mapper:
    """Applies a LeaderMap, unwrapping single-turn angles frame by frame.

    Unwrapping can only be relative to where the stream started: the encoder
    has no notion of which turn it is on. So this is a position *offset*
    estimator, not an absolute reference.
    """

    def __init__(self, mapping):
        self.mapping = mapping
        self.continuous = [None] * JOINTS

    def reset(self):
        self.continuous = [None] * JOINTS

    def to_radians(self, degrees):
        if len(degrees) != JOINTS:
            raise ValueError(f"expected {JOINTS} angles")
        result = []
        for index, (joint, angle) in enumerate(zip(self.mapping.joints, degrees)):
            previous = self.continuous[index]
            if joint.unwrap and previous is not None:
                # Shortest-path step from the last sample; the 359.9 -> 0 rollover
                # documented in docs/uart_packet.md becomes +0.1, not -359.8.
                angle = previous + ((angle - previous + 180.0) % 360.0) - 180.0
            self.continuous[index] = angle
            result.append(math.radians(joint.sign * angle + joint.offset_deg))
        return tuple(result)
