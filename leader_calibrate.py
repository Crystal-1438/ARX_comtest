"""Calibrate the leader encoders against the X5's joint coordinates.

The leader board reports single-turn absolute angles: it knows where it is on its
own circle, but not which turn it is on and nothing about how it is mounted. The
per-joint direction and zero that turn those angles into vendor joint
coordinates live in the mechanism, not in ``docs/uart_packet.md``, so they have
to be measured.

    sample   read the leader (and optionally the arm) at one hand-placed pose
    fit      turn a session of those poses into leader_map.json

The method: put the arm and the leader into the same physical pose by hand,
record both sides, and repeat at poses that differ. One pose gives the offset
once a direction is assumed; how the two sides move between poses gives the
direction. The mechanism is a 1:1 joint replica with different link lengths, and
link lengths do not affect joint angles, so the fitted slope has to come out at
+/-1. When it does not, this reports that instead of bending the numbers.

Read-only throughout: never arms, never sends a target, never changes the arm's
state beyond the SOFT mode the vendor constructor already sets.
"""

import argparse
from datetime import date
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile
import time

from app import DEFAULT_SDK, SerialInput
from leader_decoder import LeaderUartDecoder
from leader_map import JOINTS, load_mapping, uncalibrated
from protocol import ProtocolError

DEFAULT_SESSION = "calibration_session.jsonl"
MIN_POSES = 3
DEFAULT_MIN_SPAN_DEG = 30.0
DEFAULT_SLOPE_TOLERANCE = 0.05
DEFAULT_TOLERANCE_DEG = 3.0
JITTER_WARN_DEG = 0.5
MIN_FRAMES = 20


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


def build_map(results, poses, source):
    """Assemble the leader_map.json body from per-joint fits."""
    worst = max(result["max_residual_deg"] for result in results)
    comment = [
        "Generated by leader_calibrate.py; re-run fit rather than hand-editing.",
        f"Source session: {source} ({len(poses)} poses).",
        f"Worst disagreement between the matched poses: {worst:.2f} deg.",
        "The first pose of the session is the reference. Start a teleop session with",
        "the leader in that pose: unwrapping counts turns from the first frame, so a",
        "different starting pose shifts every target by a whole turn.",
        "Reference raw angles (deg): "
        + ", ".join(f"{value:.1f}" for value in poses[0]["raw_deg"]),
        f"Date: {date.today().isoformat()}.",
    ]
    return {
        "comment": comment,
        "calibrated": True,
        "joints": [
            {"sign": int(result["sign"]), "offset_deg": round(result["offset_deg"], 4),
             "unwrap": True}
            for result in results
        ],
    }


def report(results, problems):
    print("joint   leader span    slope   sign   offset_deg   max residual")
    for index, result in enumerate(results):
        if "error" in result:
            print(f"J{index + 1:<6} {'--':>10}    {'--':>7}   {'--':>4}   "
                  f"{'--':>10}   {'--':>12}")
        else:
            print(f"J{index + 1:<6} {result['span_deg']:10.2f}    {result['slope']:+.4f}   "
                  f"{int(result['sign']):+d}   {result['offset_deg']:10.3f}   "
                  f"{result['max_residual_deg']:12.2f}")
    for problem in problems:
        print(f"FAILED  {problem}")
    sys.stdout.flush()  # Keep the report ahead of the refusal that follows on stderr.


def check_map_loads(config):
    """Prove the generated map is one the loader actually accepts.

    A map that the loader rejects is worse than no map: the startup gate reads
    the same file and would wave the hardware through on it.
    """
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "leader_map.json"
        probe.write_text(json.dumps(config), encoding="utf-8")
        return load_mapping(probe)


def sample(args):
    from backends import VendorArm  # Imported here so the no-arm path never loads the SDK.

    if args.window <= 0:
        raise ValueError("--window must be positive")
    arm = None
    try:
        if args.arm:
            if not args.model:
                raise ValueError("--arm needs --model to know which URDF to load")
            # The constructor also puts the arm in SOFT. Nothing below commands it.
            arm = VendorArm(args.sdk_root, args.can_port, args.model, "soft")
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
    config = build_map(results, poses, args.session)
    check_map_loads(config)
    print()
    print(json.dumps(config, indent=2))
    if args.out:
        args.out.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
        print("Next: start the teleop session with the leader in the reference pose above.")
    else:
        print("\n(re-run with --out leader_map.json to write it)")
    return 0


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

    sampler = subcommands.add_parser("sample", help="record one hand-placed pose")
    sampler.add_argument("--serial", required=True,
                         help="leader port; use /dev/serial/by-id/, not a ttyACM number")
    sampler.add_argument("--baud", type=int, default=115200)
    sampler.add_argument("--arm", action="store_true",
                         help="also read the arm (constructs the vendor SDK, SOFT, read-only)")
    sampler.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    sampler.add_argument("--can-port", default="can0")
    sampler.add_argument("--model", choices=("2023", "2025"))
    sampler.add_argument("--out", type=Path, default=Path(DEFAULT_SESSION))
    sampler.add_argument("--window", type=positive, default=1.5)
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
    except (OSError, ValueError, ProtocolError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
