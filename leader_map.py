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
records that pose's raw angles in ``reference_deg``. That field is provenance
now, not a gate: the encoder reports one number per turn, so it cannot say which
turn it is on, and the pose the arm is actually in is the only thing that can.
``resolve_turns`` picks the whole turns from it when the operator arms.
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
# How far the leader and the arm may be apart, measured as a physical distance,
# when the operator arms. Past it the two are not in the same pose and the
# leader's first command would be a jump, so the arm is not enabled: see
# resolve_turns. Wider than the old 10 was, because this is now a hand-placement
# tolerance on two things a person lines up rather than a repeat of a stored
# number -- and because whole-turn bias removes the 0/360 disproportion that
# made the old one fire on a few degrees.
ANCHOR_TOLERANCE_DEG = 30.0


@dataclass(frozen=True)
class JointMap:
    """``sdk_deg = sign * continuous_deg + offset_deg`` for one joint."""

    sign: float = 1.0
    offset_deg: float = 0.0
    unwrap: bool = True

    def from_arm_deg(self, arm_deg):
        """The leader angle this joint's arm angle corresponds to.

        The inverse of the mapping above, and kept next to it so a change to one
        is visible from the other. ``sign`` is only ever 1 or -1, so dividing by
        it is the same as multiplying.
        """
        return (arm_deg - self.offset_deg) / self.sign


@dataclass(frozen=True)
class LeaderMap:
    joints: tuple
    calibrated: bool = False
    source: str = "<uncalibrated default>"
    # The raw leader angles at the pose the offsets were measured at, or None
    # for a map written before that was recorded. Provenance: it says where the
    # offsets come from and is what a calibration run reproduces. Nothing gates
    # on it any more -- see resolve_turns for what replaced the check.
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
    # degrees/radians mix-up rather than a pose, and would record a wrong
    # provenance for offsets that are otherwise fine.
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

    Guidance for whoever is moving the leader, and deliberately not a verdict:
    it is the shortest way round, which is what a hand can act on. The verdict
    is ``resolve_turns``, and the two agree on the size of the move once the
    whole-turn bias is in (see the test that pins them together) -- but they
    are separate functions because the sign is a direction for a person and a
    command for the mapper, and those get read differently.
    """
    return ((reference_deg - raw_deg + 180.0) % 360.0) - 180.0


def resolve_turns(continuous_deg, needed_deg, tolerance=ANCHOR_TOLERANCE_DEG):
    """Which whole turn of each encoder belongs to the pose the arm is in.

    A single-turn encoder reports one number for every turn a joint can be on,
    so 14.2 and 374.2 are the same reading and the leader alone cannot say which
    one is meant. The arm's measured pose can: it is the only thing in the loop
    that knows how many turns have gone by. This picks, per joint, the whole
    number of turns that puts the leader's reading closest to the angle that
    pose corresponds to, and reports what is left over.

    That leftover is a physical distance -- never more than half a turn, since
    the bias absorbs the rest -- and it is also the move the arm will be
    commanded to make on the next frame, once the bias is applied and ``sign``
    has flipped it. So the verdict is taken on the leftover. Taking it on the
    literal difference instead is what made a joint sitting a few degrees past
    the 0/360 rollover look like it was hundreds of degrees out.

    ``continuous_deg`` is what the mapper has unwrapped so far, one entry per
    joint, or None for a joint no frame has reached yet. That is the one case
    that cannot be answered, and it raises rather than guessing: there is no
    reading to bias.
    """
    if len(continuous_deg) != JOINTS or len(needed_deg) != JOINTS:
        raise ValueError(f"expected {JOINTS} angles")
    turns = []
    residual = []
    for now, needed in zip(continuous_deg, needed_deg):
        if now is None:
            raise ValueError("no leader frame has arrived yet")
        turn = 360.0 * round((needed - now) / 360.0)
        turns.append(turn)
        residual.append(now + turn - needed)
    worst = max(range(JOINTS), key=lambda index: abs(residual[index]))
    return {
        "ok": abs(residual[worst]) <= tolerance,
        "tolerance_deg": tolerance,
        "worst_joint": worst,
        "worst_deg": residual[worst],
        "turns_deg": turns,
        "residual_deg": residual,
    }


class Mapper:
    """Applies a LeaderMap, unwrapping single-turn angles frame by frame.

    Unwrapping can only be relative to where the stream started: the encoder
    has no notion of which turn it is on. So this is a position *offset*
    estimator, not an absolute reference.

    Which turn the stream *started* on is the same ambiguity one level up, and
    ``continuous`` cannot answer it either. ``anchor`` sets a whole-turn bias
    from the arm's measured pose to resolve it; until then the bias is zero and
    the mapping is the one the calibration run recorded.
    """

    def __init__(self, mapping):
        self.mapping = mapping
        self.continuous = [None] * JOINTS
        # Whole turns (multiples of 360) added to ``continuous`` before the
        # mapping. Kept apart from ``continuous`` on purpose: that one is the
        # unwrapped encoder reading, which the calibration tool samples and
        # which must stay a faithful record of the wire.
        self.bias = [0.0] * JOINTS

    def reset(self):
        """Forget the unwrap origin. The bias goes with it: it was chosen
        relative to that origin, so carrying it over would be worse than zero."""
        self.continuous = [None] * JOINTS
        self.bias = [0.0] * JOINTS

    def anchor(self, needed_deg, tolerance=ANCHOR_TOLERANCE_DEG):
        """Fix the whole-turn bias from the arm's pose. See ``resolve_turns``.

        Returns the verdict either way: a refusal still has to say which joints
        are out and by how much. The bias is only written when the verdict
        passes, so a session that is refused carries nothing over to the next
        attempt.
        """
        verdict = resolve_turns(self.continuous, needed_deg, tolerance)
        if verdict["ok"]:
            self.bias = list(verdict["turns_deg"])
        return verdict

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
            result.append(math.radians(
                joint.sign * (angle + self.bias[index]) + joint.offset_deg))
        return tuple(result)
