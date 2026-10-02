"""Leader single-turn encoder angles to vendor joint radians.

The leader board reports absolute single-turn angles, so it carries no zero
reference of its own. Turning them into vendor joint coordinates needs three
per-joint facts that no amount of parsing can recover: the rotation direction,
which leader angle corresponds to the vendor's zero, and whether the joint
travels more than one full turn.

Those live in a calibration file. Until it is filled in and marked
``"calibrated": true`` the mapper still runs, but only as an identity-ish
placeholder -- see ``LeaderMap.calibrated`` and the gate in ``app.py``.

The offsets are only true at the pose they were measured at, so the map also
records that pose's raw angles in ``reference_deg``, and ``check_reference``
compares a session's first frame against it.
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
TOP_FIELDS = frozenset({"calibrated", "joints", "comment", "reference_deg"})
# How far a session's first frame may sit from the calibrated pose before
# driving from it is a mistake. The offset it produces is a walk the arm makes
# unasked, so this is a small number: see check_reference.
REFERENCE_TOLERANCE_DEG = 10.0


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
    # The raw leader angles at the pose the offsets were measured at, or None
    # for a map written before that was recorded. See check_reference.
    reference_deg: tuple = None


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


def _reference(value):
    """The reference pose's raw leader angles, or None if the field is absent."""
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != JOINTS:
        raise ValueError(f"reference_deg must be a list of {JOINTS} angles")
    angles = tuple(_number(angle, f"reference_deg[{index}]")
                   for index, angle in enumerate(value))
    # A raw angle exists only within one turn of the encoder. Anything else is a
    # degrees/radians mix-up rather than a pose, and would make the startup
    # check pass or fail for the wrong reason.
    if any(not 0.0 <= angle < 360.0 for angle in angles):
        raise ValueError("reference_deg angles must be within 0..360")
    return angles


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
    unknown = set(config) - TOP_FIELDS
    if unknown:
        raise ValueError(f"leader map has unknown fields: {sorted(unknown)}")
    calibrated = config.get("calibrated", False)
    if type(calibrated) is not bool:
        raise ValueError("calibrated must be boolean")
    joints = config.get("joints")
    if not isinstance(joints, list) or len(joints) != JOINTS:
        raise ValueError(f"leader map needs exactly {JOINTS} joints")
    return LeaderMap(tuple(_joint(entry, i) for i, entry in enumerate(joints)),
                     calibrated, str(path), _reference(config.get("reference_deg")))


def shortest_turn(reference_deg, raw_deg):
    """How far to turn a joint to get from where it reads to where it must read.

    Guidance for whoever is moving the leader, and deliberately not a verdict.
    On a single-turn encoder these two quantities are different sizes: a joint
    tens of degrees from the reference reads as hundreds of degrees away, and
    the large one is what the arm will be commanded (see ``check_reference``).
    Both are worth saying -- one is the reason to refuse, the other is the
    thing to do about it -- but they must not be confused, so they live in
    separate functions with the sign carrying the direction of the turn.
    """
    return ((reference_deg - raw_deg + 180.0) % 360.0) - 180.0


def check_reference(reference_deg, raw_deg, tolerance=REFERENCE_TOLERANCE_DEG):
    """How far a session's first frame sits from the pose the map was made at.

    The offsets mean ``arm_deg - sign * raw_deg`` at the reference pose, and
    ``Mapper`` starts unwrapping from whatever the first frame reads. So a
    session that starts anywhere else shifts every target by the same amount,
    and the arm walks off by exactly that the moment it is armed. Nothing else
    in the loop can notice: the shifted position is an ordinary pose, inside the
    joint limits for any shift under a turn.

    The difference is taken literally rather than the short way round, because
    the wrap is not the small step it looks like here. Ten degrees past the
    reference on the other side of the 0/360 rollover reads as 350 degrees away
    -- and 350 degrees is what the mapper will command, because unwrapping only
    starts once this first frame has fixed the origin. So the literal
    difference *is* the commanded error, and the tolerance is applied to it.
    ``shortest_turn`` is the same pair of angles measured as a physical move;
    it belongs in the message to the operator, never in this verdict.
    """
    if len(reference_deg) != JOINTS or len(raw_deg) != JOINTS:
        raise ValueError(f"expected {JOINTS} angles")
    offsets = [now - reference for reference, now in zip(reference_deg, raw_deg)]
    worst = max(range(JOINTS), key=lambda index: abs(offsets[index]))
    return {
        "checked": True,
        "ok": abs(offsets[worst]) <= tolerance,
        "tolerance_deg": tolerance,
        "worst_joint": worst,
        "worst_deg": offsets[worst],
        "offsets_deg": offsets,
    }


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
