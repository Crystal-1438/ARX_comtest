"""Calibrate the leader encoders against the X5's joint coordinates.

The leader board reports single-turn absolute angles: it knows where it is on its
own circle, but not which turn it is on and nothing about how it is mounted. The
per-joint direction and zero that turn those angles into vendor joint
coordinates live in the mechanism, not in ``docs/uart_packet.md``, so they have
to be measured.

    session  capture poses interactively, on your own keystrokes
    sample   read the leader (and optionally the arm) at one hand-placed pose
    fit      turn a session of those poses into leader_map.json

The method: put the arm and the leader into the same physical pose by hand and
record both sides. One pose fixes the offset per joint as soon as the direction
is known, which is why ``session`` can ask for the six directions at the prompt
and write a map from a single pose -- you move a joint, watch whether the two
readings move together or apart, and answer. It also offers to check those
answers against a second pose before writing: a direction entered wrong drives
the joint backwards and still lands on a position the limits accept, so it is
worth one more pose if you have any doubt.

The longer way is still there and needs no judgement: place several poses that
differ and let ``f`` solve the directions from how the two sides move together.
The mechanism is a 1:1 joint replica with different link lengths, and link
lengths do not affect joint angles, so that fitted slope has to come out at
+/-1. When it does not, this reports that instead of bending the numbers.

The arm is never armed and never receives a target. With --arm it is put into
gravity compensation (state 3) so it carries its own weight while a hand places
it; that is a driven mode, not motor disable, and the tool hands it back to SOFT
before it exits.
"""

import argparse
import collections
from datetime import date
import functools
import json
import math
import os
from pathlib import Path
import signal
import statistics
import sys
import tempfile
import time

from app import DEFAULT_SDK, SerialInput
from leader_decoder import LeaderUartDecoder
from leader_map import JOINTS, REFERENCE_TOLERANCE_DEG, load_mapping, uncalibrated
from operator_keys import KeyInput
from protocol import ProtocolError

DEFAULT_SESSION = "calibration_session.jsonl"
DEFAULT_MAP = "leader_map.json"
DEFAULT_ARM_LOG = "calibration_arm.log"
DEFAULT_WINDOW = 1.5
MIN_POSES = 3
DEFAULT_MIN_SPAN_DEG = 30.0
DEFAULT_SLOPE_TOLERANCE = 0.05
DEFAULT_TOLERANCE_DEG = 3.0
JITTER_WARN_DEG = 0.5
MIN_FRAMES = 20
# A pose within this of the one before it on every joint adds nothing to the fit.
SAME_POSE_WARN_DEG = 5.0
# Keys the interactive session acts on. Enter and space both capture, because
# that is what a hand already on the keyboard reaches for.
CAPTURE_KEYS = frozenset("c\r\n ")
# Keys that confirm handing the arm back to SOFT once the session is over.
RELEASE_KEYS = frozenset("\r\n yg")
# Answers to the per-joint direction prompt.
DIRECTION_KEYS = frozenset("+-")
# A joint has to move this far between the reference pose and the checking pose
# before that movement says anything about its direction.
VERIFY_MIN_DEG = 5.0

GRAVITY_WARNING = (
    "the arm is now in GRAVITY COMPENSATION (state 3): the motors are driving it to\n"
    "hold its own weight. It is back-drivable, so you can place it by hand, but it is\n"
    "NOT disabled and there is no emergency stop here. Keep a hand on it, keep it\n"
    "supported, and stay with it until this tool has handed it back to SOFT.\n"
)


class SamplingDecoder(LeaderUartDecoder):
    """A leader decoder that also keeps every frame that survived validation.

    Wire parsing, range checks, the ``-1`` warm-up rule and the handshake are
    reused unchanged -- this only adds a record of what the mapper saw. The
    continuous angle is ``Mapper.continuous``, which is the unwrapped value
    *before* sign and offset, i.e. exactly the quantity a calibration solves for.
    """

    def __init__(self):
        super().__init__(uncalibrated())
        self.samples = []

    def _decode(self, fields):
        radians = super()._decode(fields)
        if radians is not None:
            self.samples.append(
                (tuple(value / 10.0 for value in fields[:JOINTS]),
                 tuple(self.mapper.continuous))
            )
        return radians


def collect(decoder, source, window, clock=time.monotonic, sleep=time.sleep):
    """Read the leader for ``window`` seconds. Returns (samples, error count)."""
    errors = 0
    deadline = clock() + window
    while clock() < deadline:
        try:
            data = source.read()
        except ProtocolError:
            # SerialInput discards its own backlog and reports it this way.
            errors += 1
            continue
        if not data:
            sleep(0.001)
            continue
        try:
            decoder.feed(data)
        except ProtocolError:
            # Counted, not fatal: this tool is not the safety path, and one
            # garbled frame should not discard a pose the operator is holding.
            errors += 1
    return decoder.samples, errors


def summarise(samples, errors, label, clock=time.monotonic):
    """Reduce a window of frames to one pose.

    The median rejects a single flipped byte; the jitter says whether the
    operator actually held still.
    """
    raw = list(zip(*[sample[0] for sample in samples]))
    continuous = list(zip(*[sample[1] for sample in samples]))
    return {
        "label": label,
        "host_monotonic": clock(),
        "frames": len(samples),
        "errors": errors,
        # Always present, null when sampled without --arm: fit has to be able to
        # tell "no arm side" from "this file predates the field".
        "arm_deg": None,
        "raw_deg": [statistics.median(column) for column in raw],
        "continuous_deg": [statistics.median(column) for column in continuous],
        "jitter_deg": [max(column) - min(column) for column in continuous],
    }


def pose_problems(pose):
    """Reasons to distrust this pose, as a list of strings."""
    problems = []
    for index, jitter in enumerate(pose["jitter_deg"]):
        if jitter > JITTER_WARN_DEG:
            problems.append(f"J{index + 1} moved {jitter:.2f} deg during the window")
    if pose["errors"]:
        problems.append(f"{pose['errors']} bad frame(s) in the window")
    return problems


def unwrap_from_reference(leader):
    """Nearest-turn correction relative to the first pose.

    Single-turn encoders cannot say which turn they are on, so the turn count has
    to come from somewhere else. It comes from the runtime convention: ``Mapper``
    unwraps by shortest path from the first frame of the session, so calibration
    pins the first sampled pose as the session's reference and measures every
    other pose the same way. A joint that really travelled more than half a turn
    between poses is then modelled as having gone the short way round, which the
    slope check in ``fit_joint`` catches rather than hides.
    """
    reference = leader[0]
    return [value + 360.0 * round((reference - value) / 360.0) for value in leader]


def shortest_delta(now, before):
    """How far one single-turn angle moved, the short way round.

    Same convention as ``Mapper``: 359.0 -> 1.0 is +2, not -358.
    """
    return ((now - before + 180.0) % 360.0) - 180.0


def least_squares(xs, ys):
    """Slope and intercept of the best line through (xs, ys)."""
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    spread = sum((x - mean_x) ** 2 for x in xs)
    if spread == 0:
        return 0.0, mean_y
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / spread
    return slope, mean_y - slope * mean_x


def fit_joint(leader, arm, min_span, slope_tolerance, tolerance):
    """Solve ``arm_deg = sign * leader_deg + offset_deg`` for one joint.

    Returns the fitted values plus the evidence behind them, or ``{"error": ...}``
    when this joint cannot be calibrated from the poses given.
    """
    continuous = unwrap_from_reference(leader)
    span = max(continuous) - min(continuous)
    if span < min_span:
        return {"error": f"leader travelled only {span:.1f} deg across the poses "
                         f"(need {min_span:.0f}); place poses that differ more"}
    slope, _ = least_squares(continuous, arm)
    if abs(abs(slope) - 1.0) > slope_tolerance:
        if abs(slope) < slope_tolerance:
            return {"error": f"leader moved {span:.1f} deg but the arm did not "
                             f"(slope {slope:+.3f}); the poses do not correspond"}
        return {"error": f"slope {slope:+.3f} is not +/-1: the joints are not 1:1, "
                         f"or one travelled more than half a turn between poses"}
    sign = 1.0 if slope > 0 else -1.0
    # Average the offset over every pose: it is the same number at each one, so
    # the spread is by-eye matching error and averaging is what removes it.
    offset = statistics.fmean(a - sign * c for c, a in zip(continuous, arm))
    residuals = [a - (sign * c + offset) for c, a in zip(continuous, arm)]
    worst = max(abs(value) for value in residuals)
    if worst > tolerance:
        pose = max(range(len(residuals)), key=lambda index: abs(residuals[index]))
        return {"error": f"poses disagree by {worst:.2f} deg (worst at pose {pose + 1}); "
                         f"the two sides are not in the same pose, or not repeatably"}
    return {
        "sign": sign,
        "offset_deg": offset,
        "slope": slope,
        "span_deg": span,
        "max_residual_deg": worst,
    }


def fit_session(poses, min_span, slope_tolerance, tolerance):
    """Fit all six joints.

    Returns (results, problems): one result per joint in J1..J6 order, so the
    report keeps its numbering when some joints fail, plus the failure messages.
    """
    if len(poses) < MIN_POSES:
        return [], [f"need at least {MIN_POSES} poses, session has {len(poses)}"]
    if any(pose.get("arm_deg") is None for pose in poses):
        return [], ["session has poses without arm angles; sample again with --arm"]
    leader = [pose["continuous_deg"] for pose in poses]
    arm = [pose["arm_deg"] for pose in poses]
    results = [
        fit_joint([values[joint] for values in leader],
                  [values[joint] for values in arm],
                  min_span, slope_tolerance, tolerance)
        for joint in range(JOINTS)
    ]
    problems = [f"J{index + 1}: {result['error']}"
                for index, result in enumerate(results) if "error" in result]
    return results, problems


def single_point_map(pose, signs):
    """Mapping entries from one pose plus the directions the operator gave.

    ``sdk_deg = sign * leader_deg + offset_deg`` is solved at this pose, and this
    pose is the reference the runtime unwrapping counts turns from -- the first
    frame of a teleop session -- so the mapping is exact here by construction.
    Offsets are deliberately not folded into +/-180: the number means literally
    ``arm_deg - sign * raw_deg`` at the reference.
    """
    return [{"sign": int(sign), "offset_deg": arm - sign * raw, "unwrap": True}
            for sign, raw, arm in zip(signs, pose["raw_deg"], pose["arm_deg"])]


def verify_directions(reference, second, signs):
    """Test hand-entered directions against a second pose.

    Movement between the two poses reveals the true direction: ``sign = +1`` says
    the two angles rise and fall together, ``-1`` says one rises as the other
    falls, so the arm step has to have the sign of ``sign * leader_step``. A joint
    that barely moved cannot say anything, so it comes back as unchecked rather
    than quietly passed.
    """
    agreed, contradicted, unmoved = [], [], []
    for index, sign in enumerate(signs):
        leader_step = shortest_delta(second["raw_deg"][index],
                                     reference["raw_deg"][index])
        arm_step = second["arm_deg"][index] - reference["arm_deg"][index]
        if abs(leader_step) < VERIFY_MIN_DEG or abs(arm_step) < VERIFY_MIN_DEG:
            unmoved.append(index)
        elif (arm_step > 0) == (sign * leader_step > 0):
            agreed.append(index)
        else:
            contradicted.append(index)
    return agreed, contradicted, unmoved


def fitted_evidence(results):
    """What the fit knows that the file's next reader should know too."""
    worst = max(result["max_residual_deg"] for result in results)
    return (
        f"Worst disagreement between the matched poses: {worst:.2f} deg.",
        "Signs and offsets were fitted to the poses above; the slope had to come out",
        "at +/-1 for every joint before this file was written.",
    )


HAND_ENTERED_EVIDENCE = (
    "Directions were entered by hand at the prompt, not solved from the data, and",
    "the offsets come from the single reference pose. A wrong direction would drive",
    "that joint backwards and still look like a plausible position, so if the arm",
    "ever mirrors a movement, re-check the signs here first.",
)


def build_map(joints, poses, source, evidence):
    """Assemble the leader_map.json body from six ``{"sign", "offset_deg"}`` entries."""
    # ``single_point_map`` solves the offsets at this pose's raw angles, and the
    # runtime mapper unwraps from whatever its first frame reads, so the raw
    # angles of pose 1 are the pose a teleop session has to start in. Raw rather
    # than continuous: pose 1's continuous angle depends on where the *session*
    # began, which is not something a later run can reproduce.
    reference = [round(value, 1) for value in poses[0]["raw_deg"]]
    comment = [
        "Generated by leader_calibrate.py; re-run the tool rather than hand-editing.",
        f"Source session: {source} ({len(poses)} pose(s)).",
        *evidence,
        "The first pose of the session is the reference, and reference_deg below is",
        "its raw leader angles. Start a teleop session with the leader in that pose:",
        "the mapper unwraps from the first frame it sees, so starting anywhere else",
        "shifts every target by that much, and the arm walks off by it as soon as it",
        f"is armed. app.py refuses to arm while any joint is more than "
        f"{REFERENCE_TOLERANCE_DEG:.0f} deg away.",
        "Reference raw angles (deg): " + ", ".join(f"{value:.1f}" for value in reference),
        f"Date: {date.today().isoformat()}.",
    ]
    return {
        "comment": comment,
        "calibrated": True,
        "reference_deg": reference,
        "joints": [
            {"sign": int(joint["sign"]), "offset_deg": round(joint["offset_deg"], 4),
             "unwrap": True}
            for joint in joints
        ],
    }


def fitted_joints(results):
    """The six map entries a successful ``fit_session`` describes."""
    return [{"sign": result["sign"], "offset_deg": result["offset_deg"]}
            for result in results]


def report(results, problems, stream=sys.stdout):
    """Print the per-joint table. ``stream`` is the console, not the SDK log."""
    print("joint   leader span    slope   sign   offset_deg   max residual", file=stream)
    for index, result in enumerate(results):
        if "error" in result:
            print(f"J{index + 1:<6} {'--':>10}    {'--':>7}   {'--':>4}   "
                  f"{'--':>10}   {'--':>12}", file=stream)
        else:
            print(f"J{index + 1:<6} {result['span_deg']:10.2f}    {result['slope']:+.4f}   "
                  f"{int(result['sign']):+d}   {result['offset_deg']:10.3f}   "
                  f"{result['max_residual_deg']:12.2f}", file=stream)
    for problem in problems:
        print(f"FAILED  {problem}", file=stream)
    stream.flush()  # Keep the report ahead of the refusal that follows on stderr.


def check_map_loads(config):
    """Prove the generated map is one the loader actually accepts.

    A map that the loader rejects is worse than no map: the startup gate reads
    the same file and would wave the hardware through on it.
    """
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "leader_map.json"
        probe.write_text(json.dumps(config), encoding="utf-8")
        return load_mapping(probe)


def confirm_release(arm, keys, console, sleep=time.sleep):
    """Hand the arm back to SOFT, but only once the operator says it is safe.

    Returning to SOFT means zero torque: the arm drops to whatever is holding it.
    Doing that the instant the session ends would drop it while the operator is
    still at the keyboard, and skipping it would leave the arm driven with no
    process left on the CAN bus. So the arm keeps holding until someone who can
    see the arm confirms. Returns True when the operator confirmed.
    """
    console.write("\nthe arm is still in GRAVITY COMPENSATION, holding itself up.\n"
                  "check that it is supported, then press Enter to hand it back to SOFT\n"
                  "(zero torque -- it will sag onto the support).\n")
    console.flush()
    while True:
        for key in keys.read_keys():
            if key in RELEASE_KEYS:
                arm.stop()
                console.write("arm returned to SOFT.\n")
                return True
        if keys.exhausted:
            console.write("stdin closed; returning the arm to SOFT.\n")
            arm.stop()
            return False
        sleep(0.05)


def _raise_interrupt(_signum, _frame):
    raise KeyboardInterrupt


def treat_sigterm_as_interrupt(function):
    """Make the arm-driving subcommands clean up on SIGTERM, not just on Ctrl-C.

    Python already turns SIGINT into KeyboardInterrupt, but SIGTERM's default
    action ends the process where it stands: the finally chain that hands the arm
    back to SOFT would never run, leaving a driven arm with no process behind it.
    Raising instead reuses the Ctrl-C path end to end, at the cost of reporting
    exit code 130 for a termination too.
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            previous = signal.signal(signal.SIGTERM, _raise_interrupt)
        except ValueError:  # Not the main thread; signal.signal refuses.
            return function(*args, **kwargs)
        try:
            return function(*args, **kwargs)
        finally:
            signal.signal(signal.SIGTERM, previous)

    return wrapper


@treat_sigterm_as_interrupt
def sample(args):
    from backends import VendorArm  # Imported here so the no-arm path never loads the SDK.

    if args.window <= 0:
        raise ValueError("--window must be positive")
    arm = None
    holding = False
    try:
        if args.arm:
            if not args.model:
                raise ValueError("--arm needs --model to know which URDF to load")
            # The constructor puts the arm in SOFT; --arm then hands it to gravity
            # compensation so a hand can place it for the pose.
            arm = VendorArm(args.sdk_root, args.can_port, args.model, "soft")
            arm.enable_gravity_compensation()
            holding = True
            print(GRAVITY_WARNING, end="")
        source = SerialInput(args.serial, args.baud)
        try:
            samples, errors = collect(SamplingDecoder(), source, args.window)
        finally:
            source.close()
        if len(samples) < MIN_FRAMES:
            raise ValueError(f"only {len(samples)} frames in {args.window}s; check the "
                             f"port with ls -l /dev/serial/by-id/ and that the board is on")
        pose = summarise(samples, errors, args.label)
        if arm is not None:
            pose["arm_deg"] = [math.degrees(value) for value in arm.read_joints()]
    finally:
        if arm is not None:
            if holding:
                # No terminal to ask on here, so say what is about to happen instead.
                print("\narm: handing back to SOFT (zero torque) -- it will sag onto "
                      "its support.")
            arm.close()

    with open(args.out, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(pose) + "\n")
    with open(args.out, encoding="utf-8") as stream:
        recorded = sum(1 for _ in stream)

    print(f"pose {recorded}  ({pose['frames']} frames, {pose['errors']} bad)"
          + (f"  label={pose['label']}" if pose["label"] else ""))
    for index in range(JOINTS):
        arm_deg = "" if arm is None else f"{pose['arm_deg'][index]:8.2f}"
        print(f"  J{index + 1}: leader {pose['raw_deg'][index]:7.1f} deg "
              f"(jitter {pose['jitter_deg'][index]:5.2f})   arm {arm_deg}")
    for problem in pose_problems(pose):
        print(f"  warning: {problem}")
    print(f"recorded to {args.out}")
    return 0


def fit(args):
    poses = load_session(args.session)
    results, problems = fit_session(poses, args.min_span, args.slope_tolerance,
                                    args.tolerance)
    report(results, problems)
    if problems:
        # With no results the session itself is unusable (too few poses, no arm
        # side); with results, the joints that failed are the ones to re-pose.
        reason = (f"{len(problems)} joint(s) failed; re-place those poses"
                  if results else "the session cannot be fitted yet")
        print(f"\nrefusing to write a map: {reason}.", file=sys.stderr)
        return 2
    config = build_map(fitted_joints(results), poses, args.session, fitted_evidence(results))
    check_map_loads(config)
    print()
    print(json.dumps(config, indent=2))
    if args.out:
        args.out.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
        print("Next: start the teleop session with the leader in the reference pose above "
              f"(within {REFERENCE_TOLERANCE_DEG:.0f} deg on every joint).")
    else:
        print("\n(re-run with --out leader_map.json to write it)")
    return 0


class VendorChatter:
    """Keep the vendor SDK's console output out of the operator's display.

    The core library prints from C++ (it announces itself, and its destructor
    announces the motors it releases), so redirecting ``sys.stdout`` would not
    catch it: this moves the file descriptors instead. What it wrote is kept in a
    log rather than discarded, since it is the only trace of what its threads did.
    """

    def __init__(self, path):
        self.path = path
        self.console_fd = None
        self.error_fd = None
        self.console = None
        self.log = None

    def __enter__(self):
        sys.stdout.flush()
        sys.stderr.flush()
        self.log = open(self.path, "ab")
        # Two separate duplicates: 1 and 2 are usually the same terminal, but
        # restoring 2 from the duplicate of 1 would lose a redirected stderr.
        self.console_fd = os.dup(1)
        self.error_fd = os.dup(2)
        self.console = open(self.console_fd, "w", buffering=1, encoding="utf-8")
        os.dup2(self.log.fileno(), 1)
        os.dup2(self.log.fileno(), 2)
        return self.console

    def __exit__(self, *exception):
        try:
            self.console.flush()
        finally:
            # Restore first, close second: the console object owns console_fd,
            # and 1 and 2 are our own duplicates by the time they go.
            os.dup2(self.console_fd, 1)
            os.dup2(self.error_fd, 2)
            self.console.close()
            os.close(self.error_fd)
            self.log.close()
        return False


class InteractiveSession:
    """Pose-by-pose capture on the operator's own keystrokes.

    Both sides stay open for the whole session: starting the SDK is expensive,
    and the operator wants to watch the arm's angles track the leader while they
    drag it into place. So unlike ``sample``, which opens and closes per pose,
    this owns a live loop and captures from a trailing window when told to.

    The window is why the captured pose is the one the operator just held: at
    200 Hz the last ``--window`` seconds are the pose on screen right now.
    """

    def __init__(self, source, arm, keys, stream, session_path, map_path,
                 window=DEFAULT_WINDOW, min_span=DEFAULT_MIN_SPAN_DEG,
                 slope_tolerance=DEFAULT_SLOPE_TOLERANCE,
                 tolerance=DEFAULT_TOLERANCE_DEG,
                 clock=time.monotonic, sleep=time.sleep, plain=False):
        self.source = source
        self.arm = arm
        self.keys = keys
        self.stream = stream
        self.emit = stream.write
        self.session_path = session_path
        self.map_path = map_path
        self.window = window
        self.min_span = min_span
        self.slope_tolerance = slope_tolerance
        self.tolerance = tolerance
        self.clock = clock
        self.sleep = sleep
        self.plain = plain
        self.decoder = SamplingDecoder()
        self.recent = collections.deque()
        self.poses = []
        self.errors = 0
        self.arm_deg = None
        self.arm_error = None
        self.drawn = 0
        self.finished = False
        self.wrote_map = False
        self.directions = []   # +/-1 per joint, as the operator answered them
        self.awaiting = None   # "direction" or "verify" while a prompt owns the keys
        self.message = "drag both sides into the same pose, then press c"

    # -- live input ---------------------------------------------------------

    def read_leader(self):
        """One non-blocking pull from the leader, into the trailing window."""
        try:
            data = self.source.read()
        except ProtocolError:
            self.errors += 1
            return
        if not data:
            return
        try:
            self.decoder.feed(data)
        except ProtocolError:
            self.errors += 1
        # Frames the decoder accepted before a garbled one are still good, so
        # drain whatever landed either way.
        for raw, continuous in self.decoder.samples:
            self.recent.append((self.clock(), raw, continuous))
        del self.decoder.samples[:]  # The trailing window below is what we keep.
        cutoff = self.clock() - self.window
        while self.recent and self.recent[0][0] < cutoff:
            self.recent.popleft()

    def read_arm(self):
        if self.arm is None:
            return
        try:
            self.arm_deg = [math.degrees(value) for value in self.arm.read_joints()]
            self.arm_error = None
        except Exception as exc:  # The vendor SDK raises its own types.
            self.arm_deg = None
            self.arm_error = str(exc)

    def window_pose(self):
        """The pose on screen right now, from the trailing window."""
        if not self.recent:
            return None
        return summarise([(sample[1], sample[2]) for sample in self.recent],
                         self.errors, f"pose {len(self.poses) + 1}", self.clock)

    # -- actions ------------------------------------------------------------

    def capture(self):
        pose = self.window_pose()
        if pose is None or pose["frames"] < MIN_FRAMES:
            frames = 0 if pose is None else pose["frames"]
            self.message = (f"only {frames} leader frame(s) in the last "
                            f"{self.window:.1f}s -- is the board on?")
            return False
        if self.arm is not None:
            # Fresh at capture time rather than the display's reading: the arm
            # side of this pose is the measurement, not decoration.
            self.read_arm()
            if self.arm_deg is None:
                self.message = f"could not read the arm: {self.arm_error}"
                return False
            pose["arm_deg"] = self.arm_deg
        self.poses.append(pose)
        self.errors = 0  # Per-pose: one bad frame early should not taint the rest.
        self.message = f"captured pose {len(self.poses)}"
        problems = pose_problems(pose)
        if problems:
            self.message += " -- " + "; ".join(problems)
        elif len(self.poses) > 1:
            moved = max(abs(now - before) for now, before in
                        zip(pose["continuous_deg"], self.poses[-2]["continuous_deg"]))
            if moved < SAME_POSE_WARN_DEG:
                self.message += " -- nearly the same pose as the last one"
        return True

    def undo(self):
        if not self.poses:
            self.message = "nothing to undo"
            return
        self.message = f"dropped pose {len(self.poses)}"
        self.poses.pop()

    def joints_needing_range(self):
        """Joints whose captured poses are still too close together to fit."""
        if len(self.poses) < 2:
            return list(range(JOINTS))
        columns = list(zip(*[pose["continuous_deg"] for pose in self.poses]))
        return [index for index, column in enumerate(columns)
                if max(column) - min(column) < self.min_span]

    def span_note(self):
        if not self.poses:
            return "all six (no poses yet)"
        needing = self.joints_needing_range()
        if not needing:
            return "none"
        return " ".join(f"J{index + 1}" for index in needing)

    def save_session(self):
        """Rewrite the session file from the poses in hand, for a later ``fit``."""
        if not self.poses or self.session_path is None:
            return None
        with open(self.session_path, "w", encoding="utf-8") as stream:
            for pose in self.poses:
                stream.write(json.dumps(pose) + "\n")
        return self.session_path

    def write_map(self, config):
        """Validate, show and store a map. The file the loader takes is written last."""
        check_map_loads(config)
        text = json.dumps(config, indent=2)
        self.emit("\n" + text + "\n\n")
        if self.map_path is not None:
            self.map_path.write_text(text + "\n", encoding="utf-8")
            self.wrote_map = True
            self.emit(f"wrote {self.map_path}\n")
            self.emit("Next: start the teleop session with the leader in the reference "
                      f"pose,\npose 1 ({', '.join(f'{v:.1f}' for v in self.poses[0]['raw_deg'])} "
                      "raw deg).\napp.py refuses to arm until every joint is within "
                      f"{REFERENCE_TOLERANCE_DEG:.0f} deg of that.\n")
        else:
            self.emit("\n(no --map given; nothing written)\n")
        self.finished = True

    def finish(self):
        """Fit, validate and write the map. False leaves the loop running."""
        results, problems = fit_session(self.poses, self.min_span, self.slope_tolerance,
                                        self.tolerance)
        report(results, problems, stream=self.stream)
        if problems:
            if results:
                self.message = (f"{len(problems)} joint(s) failed -- press u to undo a "
                                f"pose, or place more of them")
            else:
                self.message = f"{problems[0]} -- keep going"
            self.drawn = 0  # The report scrolled past the display; redraw from the top.
            return False
        source = self.save_session() or "<interactive session>"
        self.write_map(build_map(fitted_joints(results), self.poses, source,
                                 fitted_evidence(results)))
        return True

    # -- one pose plus the operator's own directions -------------------------

    def live_step(self, index):
        """How far one joint has moved since the reference pose, right now.

        While a direction is being asked for, this is the evidence: move the joint
        one way and see whether the two numbers move together or apart.
        """
        pose = self.window_pose()
        if pose is None or not self.poses:
            return None
        leader = shortest_delta(pose["raw_deg"][index], self.poses[0]["raw_deg"][index])
        arm = None
        if self.arm_deg is not None and self.poses[0].get("arm_deg") is not None:
            arm = self.arm_deg[index] - self.poses[0]["arm_deg"][index]
        return leader, arm

    def start_directions(self):
        """Ask for one direction per joint, in order, starting at J1."""
        if self.arm is None:
            self.message = "directions need the arm side: restart with --arm"
        elif not self.poses:
            self.message = "capture the reference pose first (c), then press d"
        else:
            self.directions = []
            self.awaiting = "direction"
            self.message = "move joint 1 and watch the two columns"

    def answer_direction(self, key):
        if key == "x":
            self.awaiting = None
            self.message = "directions cancelled; the pose is still here"
            return
        if key in ("\x7f", "\b"):
            # Backing up one joint is cheaper than starting the six over.
            if self.directions:
                self.directions.pop()
                self.message = (f"back to joint {len(self.directions) + 1}: same way (+) "
                                f"or opposite (-)?")
            return
        if key not in DIRECTION_KEYS:
            return
        self.directions.append(1.0 if key == "+" else -1.0)
        if len(self.directions) == JOINTS:
            self.awaiting = "verify"
            self.message = "press c on a different pose to check these, or enter to write"
        else:
            self.message = (f"joint {len(self.directions) + 1}: same way (+) or "
                            f"opposite (-)?")

    def answer_verify(self, key):
        if key == "x":
            self.awaiting = None
            self.message = "nothing written; press d to redo the directions"
            return
        if key in ("\r", "\n", " "):
            # Checking is optional: this is the "I am sure" path.
            self.write_directions_map()
            return
        if key != "c":
            return
        self.capture()
        if len(self.poses) < 2:  # capture() refused; it has said why.
            return
        agreed, contradicted, unmoved = verify_directions(self.poses[0], self.poses[-1],
                                                          self.directions)
        if contradicted:
            self.awaiting = None
            named = " ".join(f"J{index + 1}" for index in contradicted)
            self.message = (f"the second pose contradicts {named} -- press d to redo "
                            "the directions, or move those joints further")
            if unmoved:
                self.message += "; not checked: " + " ".join(f"J{i + 1}" for i in unmoved)
            return
        if not agreed:
            # Asked for a check and got nothing checkable: writing now would look
            # like a pass. Stay here so the operator can move a joint and retry.
            self.message = ("that pose is too close to the reference to check anything -- "
                            "move the joints further and press c again, or enter to write "
                            "them unchecked")
            return
        self.emit(f"\nchecked {len(agreed)} joint(s) against the second pose")
        if unmoved:
            self.emit(" -- moved too little to check: "
                      + " ".join(f"J{i + 1}" for i in unmoved))
        self.emit("\n")
        self.directions_map()

    def write_directions_map(self):
        """Write the map straight away, with the directions the operator gave."""
        self.emit("\nnot checked against a second pose.\n")
        self.directions_map()

    def directions_map(self):
        """Build the map from the reference pose and the entered directions."""
        joints = single_point_map(self.poses[0], self.directions)
        source = self.save_session() or "<interactive session>"
        self.awaiting = None
        self.write_map(build_map(joints, self.poses, source, HAND_ENTERED_EVIDENCE))

    def handle(self, key):
        if self.awaiting == "direction":
            self.answer_direction(key)
        elif self.awaiting == "verify":
            self.answer_verify(key)
        elif key in CAPTURE_KEYS:
            self.capture()
        elif key == "d":
            self.start_directions()
        elif key == "u":
            self.undo()
        elif key == "f":
            self.finish()
        elif key == "h":
            self.message = ("c/enter capture, d directions from one pose, f fit poses and "
                            "write, u undo, q quit; drag the arm by hand -- gravity "
                            "compensation holds it up")
        elif key == "q":
            self.finished = True
        elif key in ("\x03", "\x04"):  # Ctrl-C/Ctrl-D if ISIG is ever off.
            self.finished = True

    # -- display and loop ---------------------------------------------------

    def draw(self):
        pose = self.window_pose()
        if self.arm is None:
            headline = "leader calibration -- no arm attached, nothing is commanded"
        else:
            headline = ("leader calibration -- the arm is in GRAVITY COMPENSATION "
                        "(motor-driven, hand-guidable); no target is sent")
        lines = [headline, ""]
        lines.append("     leader deg   jitter      arm deg")
        # The joint being asked about is the one the operator has to move now.
        asking = len(self.directions) if self.awaiting == "direction" else None
        for index in range(JOINTS):
            mark = ">" if index == asking else " "
            if pose is None:
                lines.append(f"{mark} J{index + 1}        --       --          --")
                continue
            arm_cell = "--" if self.arm_deg is None else f"{self.arm_deg[index]:.2f}"
            lines.append(f"{mark} J{index + 1} {pose['raw_deg'][index]:9.1f}   "
                         f"{pose['jitter_deg'][index]:5.2f}   {arm_cell:>9}")
        frames = 0 if pose is None else pose["frames"]
        lines.append("")
        lines.append(f"  {frames} frames, {self.errors} bad   |   poses: {len(self.poses)}"
                     f"   |   still needing range (for f): {self.span_note()}")
        if asking is not None:
            lines.append(f"  J{asking + 1} direction: + if the arm angle rises when the "
                         f"leader angle rises, - if it falls")
            step = self.live_step(asking)
            if step is not None:
                arm_cell = "arm --" if step[1] is None else f"arm {step[1]:+.1f}"
                lines.append(f"  moved since the pose: leader {step[0]:+.1f}   {arm_cell}"
                             f"   [backspace] back   [x] cancel")
        elif self.awaiting == "verify":
            lines.append("  directions recorded -- [c] check them against a DIFFERENT pose,"
                         " enter writes them unchecked   [x] cancel")
        else:
            lines.append("  [c] capture  [d] directions from one pose  [f] fit poses"
                         "  [u] undo  [q] quit  [h] help")
        lines.append("  " + self.message)
        text = "\n".join(lines)
        if self.plain:
            self.emit(text + "\n\n")
            return
        if self.drawn:
            self.emit(f"\x1b[{self.drawn}A")  # Back up over the last block.
        self.emit(text + "\x1b[J\n")
        self.drawn = len(lines) + 1

    def step(self):
        self.read_leader()
        self.read_arm()
        for key in self.keys.read_keys():
            self.handle(key)
        self.draw()
        self.sleep(0.25)

    def run(self):
        # An interrupt is deliberately left to propagate: the finally still keeps
        # the poses, but the caller must not go on to prompt for a graceful release
        # when the operator has just hit Ctrl-C.
        try:
            while not self.finished and not self.keys.exhausted:
                self.step()
        finally:
            if not self.plain and self.drawn:
                self.emit("\n")
            # Always leave the poses behind, even when the operator quit early:
            # re-placing them costs more than re-running fit costs.
            if self.poses:
                self.emit(f"\n{len(self.poses)} pose(s) kept in {self.session_path}\n")
            self.save_session()
        if self.wrote_map or not self.poses:
            return 0
        self.emit(f"no map written: {len(self.poses)} pose(s) are in {self.session_path}, "
                  f"which 'fit' can use when you are ready\n")
        return 2


@treat_sigterm_as_interrupt
def session(args):
    """Run the interactive capture loop against real hardware."""
    from backends import VendorArm  # Imported here so the no-arm path never loads the SDK.

    if args.window <= 0:
        raise ValueError("--window must be positive")
    keys = KeyInput()
    try:
        # Without a terminal the loop would spin until stdin closes and then
        # report "nothing captured", which reads as a hardware problem.
        if keys.fd is None or not os.isatty(keys.fd):
            raise ValueError("stdin is not a terminal; run this from a shell you can "
                             "type in, or use the 'sample' subcommand instead")
        # Everything that touches the vendor SDK runs under the redirect: its
        # constructor and its destructor both print from C++.
        with VendorChatter(args.arm_log) as console:
            arm = None
            holding = released = False
            if args.arm:
                if not args.model:
                    raise ValueError("--arm needs --model to know which URDF to load")
                console.write(f"starting the vendor SDK; its output goes to "
                              f"{args.arm_log}\n")
                arm = VendorArm(args.sdk_root, args.can_port, args.model, "soft")
            try:
                if arm is not None:
                    # --arm means "hold the arm up for me while I place it", so
                    # entering gravity compensation is the point of the flag, not
                    # an extra option. Inside the try: a failure here must still
                    # run close(), or the arm stays driven with nothing to undo it.
                    arm.enable_gravity_compensation()
                    holding = True
                    console.write(GRAVITY_WARNING)
                source = SerialInput(args.serial, args.baud)
                try:
                    live = InteractiveSession(
                        source=source, arm=arm, keys=keys, stream=console,
                        session_path=args.out, map_path=args.map, window=args.window,
                        min_span=args.min_span, slope_tolerance=args.slope_tolerance,
                        tolerance=args.tolerance, plain=args.plain)
                    code = live.run()
                finally:
                    source.close()
                # Ctrl-C skips this: a propagating interrupt means the operator wants
                # out now, not a question, and close() still returns the arm to SOFT.
                if arm is not None:
                    released = confirm_release(arm, keys, console)
                return code
            finally:
                if arm is not None:
                    if holding and not released:
                        console.write("\narm: handing back to SOFT (zero torque) -- "
                                      "it will sag onto its support.\n")
                        console.flush()
                    arm.close()
    finally:
        keys.close()


def load_session(path):
    poses = []
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue
            try:
                poses.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
    return poses


def positive(value):
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Calibrate the leader encoders against the X5's joint coordinates.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    live = subcommands.add_parser(
        "session", help="capture poses interactively; one pose plus directions is "
                        "enough, several poses can be fitted instead")
    live.add_argument("--serial", required=True,
                      help="leader port; use /dev/serial/by-id/, not a ttyACM number")
    live.add_argument("--baud", type=int, default=115200)
    live.add_argument("--arm", action="store_true",
                      help="also read the arm; puts it in gravity compensation so it "
                           "holds itself up, and asks before handing it back to SOFT")
    live.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    live.add_argument("--can-port", default="can0")
    live.add_argument("--model", choices=("2023", "2025"))
    live.add_argument("--out", type=Path, default=Path(DEFAULT_SESSION),
                      help="where the captured poses are kept")
    live.add_argument("--map", type=Path, default=Path(DEFAULT_MAP),
                      help="where a successful fit is written")
    live.add_argument("--window", type=positive, default=DEFAULT_WINDOW,
                      help="seconds of leader history one capture covers")
    live.add_argument("--min-span", type=positive, default=DEFAULT_MIN_SPAN_DEG)
    live.add_argument("--slope-tolerance", type=positive, default=DEFAULT_SLOPE_TOLERANCE)
    live.add_argument("--tolerance", type=positive, default=DEFAULT_TOLERANCE_DEG)
    live.add_argument("--arm-log", type=Path, default=Path(DEFAULT_ARM_LOG),
                      help="the vendor SDK prints from C++; this is where it goes")
    live.add_argument("--plain", action="store_true",
                      help="scroll the readout instead of redrawing it in place")
    live.set_defaults(handler=session)

    sampler = subcommands.add_parser("sample", help="record one hand-placed pose")
    sampler.add_argument("--serial", required=True,
                         help="leader port; use /dev/serial/by-id/, not a ttyACM number")
    sampler.add_argument("--baud", type=int, default=115200)
    sampler.add_argument("--arm", action="store_true",
                         help="also read the arm; puts it in gravity compensation while "
                              "the pose is read, then hands it back to SOFT")
    sampler.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    sampler.add_argument("--can-port", default="can0")
    sampler.add_argument("--model", choices=("2023", "2025"))
    sampler.add_argument("--out", type=Path, default=Path(DEFAULT_SESSION))
    sampler.add_argument("--window", type=positive, default=DEFAULT_WINDOW)
    sampler.add_argument("--label")
    sampler.set_defaults(handler=sample)

    fitter = subcommands.add_parser("fit", help="turn a session into leader_map.json")
    fitter.add_argument("session", type=Path)
    fitter.add_argument("--out", type=Path)
    fitter.add_argument("--min-span", type=positive, default=DEFAULT_MIN_SPAN_DEG)
    fitter.add_argument("--slope-tolerance", type=positive, default=DEFAULT_SLOPE_TOLERANCE)
    fitter.add_argument("--tolerance", type=positive, default=DEFAULT_TOLERANCE_DEG)
    fitter.set_defaults(handler=fit)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except (OSError, ValueError, ProtocolError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
