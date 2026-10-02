import io
import json
import math
import os
from pathlib import Path
import pty
import select
import signal
import tempfile
import threading
import time
import unittest
from unittest import mock

from leader_calibrate import (
    JITTER_WARN_DEG, MIN_FRAMES, MIN_POSES, InteractiveSession, SamplingDecoder,
    VendorChatter, build_map, check_map_loads, collect, confirm_release, fit_joint,
    fit_session, least_squares, load_session, main, pose_problems, summarise,
    treat_sigterm_as_interrupt, unwrap_from_reference,
)
from leader_map import Mapper, load_mapping

# Six leader poses and the per-joint offsets the arm angles are built from, so a
# correct fit has to recover exactly these numbers. Every joint moves well past
# the 30 degree minimum span used by the fit.
OFFSETS = [12.5, -30.0, 45.25, 0.0, -120.75, 200.0]
LEADER_POSES = [
    [81.7, 19.1, 106.0, 256.8, 299.3, 201.6],
    [140.2, 75.4, 40.5, 300.1, 250.0, 150.9],
    [20.9, 120.7, 150.8, 210.3, 330.7, 260.4],
    [95.5, 95.5, 90.0, 275.0, 310.0, 180.0],
]


def line(*fields):
    """One leader packet, as the board sends it."""
    return (",".join(str(field) for field in fields) + "\r\n").encode()


def arm_for(leader):
    return [value + offset for value, offset in zip(leader, OFFSETS)]


def session(leader_poses=LEADER_POSES):
    """A session as sample() would have written it."""
    return [{"raw_deg": list(leader), "continuous_deg": list(leader),
             "arm_deg": arm_for(leader)} for leader in leader_poses]


def fit_column(poses, joint, min_span=30.0, tolerance=3.0):
    return fit_joint([pose["continuous_deg"][joint] for pose in poses],
                     [pose["arm_deg"][joint] for pose in poses],
                     min_span, 0.05, tolerance)


def payload(pose, count=MIN_FRAMES + 5):
    """One pose, held, as the board would stream it."""
    return line(*(int(round(value * 10)) for value in pose), 500) * count


class Clock:
    """A clock the test moves, so the trailing window is deterministic."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class Feeder:
    """A leader port that hands out one payload per read and advances time."""

    def __init__(self, payloads, clock, step=2.0, on_read=None):
        self.payloads = list(payloads)
        self.clock = clock
        self.step = step
        self.on_read = on_read

    def read(self):
        if not self.payloads:
            return b""
        self.clock.now += self.step
        if self.on_read is not None:
            self.on_read()
        return self.payloads.pop(0)


class FakeArm:
    """Returns each pose in turn, and advances only when the operator moves on."""

    def __init__(self, poses):
        self.poses = list(poses)
        self.index = -1  # Advanced by the leader port: delivering a pose places it.
        self.error = None
        self.closed = False

    def advance(self):
        self.index = min(self.index + 1, len(self.poses) - 1)

    def read_joints(self):
        if self.error is not None:
            raise self.error
        return [math.radians(value) for value in self.poses[max(self.index, 0)]]

    def close(self):
        self.closed = True


class FakeKeys:
    """A scripted keyboard: one entry per poll, then silence."""

    def __init__(self, script):
        self.script = list(script)
        self.exhausted = False

    def read_keys(self):
        return self.script.pop(0) if self.script else ""


class FitTests(unittest.TestCase):
    def test_recovers_known_offsets_and_slope_one(self):
        poses = session()
        for joint, offset in enumerate(OFFSETS):
            with self.subTest(joint=joint):
                result = fit_column(poses, joint)
                self.assertNotIn("error", result)
                self.assertEqual(result["sign"], 1.0)
                self.assertAlmostEqual(result["offset_deg"], offset, places=6)
                self.assertAlmostEqual(result["slope"], 1.0, places=6)
                self.assertAlmostEqual(result["max_residual_deg"], 0.0, places=6)

    def test_recovers_a_reversed_joint(self):
        # Mounted the other way round: the arm angle falls as the leader rises.
        leader = [pose[2] for pose in LEADER_POSES]
        arm = [-value + 45.25 for value in leader]
        result = fit_joint(leader, arm, 30.0, 0.05, 3.0)
        self.assertEqual(result["sign"], -1.0)
        self.assertAlmostEqual(result["offset_deg"], 45.25, places=6)

    def test_an_imperfect_operator_still_calibrates(self):
        # Matching two arms by eye is worth about a degree. The offset is the
        # average over the poses, so that spread does not end up in the map.
        poses = session()
        for pose, noise in zip(poses, [0.4, -0.9, 1.2, -0.5]):
            pose["arm_deg"] = [value + noise for value in pose["arm_deg"]]
        result = fit_column(poses, 0)
        self.assertNotIn("error", result)
        self.assertLessEqual(result["max_residual_deg"], 3.0)
        self.assertAlmostEqual(result["offset_deg"], OFFSETS[0], delta=1.0)

    def test_a_joint_the_operator_never_moved_cannot_be_calibrated(self):
        poses = session([LEADER_POSES[0]] * 4)
        result = fit_column(poses, 0)
        self.assertIn("travelled only", result["error"])

    def test_poses_that_do_not_correspond_are_rejected(self):
        # The leader moved a long way while the arm stayed put. That is a slope
        # near zero, not a valid mapping with a large offset.
        poses = session()
        for pose in poses:
            pose["arm_deg"] = [10.0] * 6
        result = fit_column(poses, 0)
        self.assertIn("the arm did not", result["error"])

    def test_a_geared_joint_is_reported_rather_than_forced(self):
        leader = [pose[0] for pose in LEADER_POSES]
        result = fit_joint(leader, [2.0 * value for value in leader], 30.0, 0.05, 3.0)
        self.assertIn("not +/-1", result["error"])

    def test_inconsistent_poses_are_rejected(self):
        # Some poses put the arm somewhere the leader does not imply: the
        # operator matched those wrong. The shifts are laid out so the line
        # still has slope 1, which is the point -- what fails here is the
        # disagreement between poses, not the shape of the line.
        poses = session()
        for pose, shift in zip(poses, [5.0, -5.0, -5.0, 5.0]):
            pose["arm_deg"][3] += shift
        result = fit_column(poses, 3)
        self.assertIn("disagree", result["error"])

    def test_the_leader_span_is_measured_over_the_unwrapped_angle(self):
        poses = session()
        result = fit_column(poses, 0)
        self.assertAlmostEqual(result["span_deg"], 140.2 - 20.9, places=6)


class WrapTests(unittest.TestCase):
    """Single-turn encoders roll 359.9 -> 0.0, so poses may straddle that."""

    def test_a_pose_read_across_the_rollover_fits(self):
        # J1 physically at 350 then at 10, having gone the short way round.
        leader = [350.0, 10.0, 0.0, 340.0]
        arm = [value + OFFSETS[0] for value in [350.0, 370.0, 360.0, 340.0]]
        result = fit_joint(leader, arm, 30.0, 0.05, 3.0)
        self.assertNotIn("error", result)
        self.assertEqual(result["sign"], 1.0)
        self.assertAlmostEqual(result["offset_deg"], OFFSETS[0], places=6)

    def test_the_first_pose_defines_the_turn_count(self):
        # The same two readings, sampled in the other order: the fit follows the
        # runtime convention, where unwrapping starts at the session's first frame.
        self.assertAlmostEqual(
            fit_joint([30.0, 350.0], [390.0, 350.0], 30.0, 0.05, 3.0)["offset_deg"],
            360.0, places=6)
        self.assertAlmostEqual(
            fit_joint([350.0, 30.0], [350.0, 390.0], 30.0, 0.05, 3.0)["offset_deg"],
            0.0, places=6)

    def test_unwrap_measures_from_the_first_pose(self):
        self.assertEqual(unwrap_from_reference([10.0, 350.0, 20.0]), [10.0, -10.0, 20.0])

    def test_a_joint_that_really_went_the_long_way_is_caught(self):
        # True travel +200 deg, which a single-turn encoder cannot tell from
        # -160. The shortest path is what the runtime decoder will assume, so the
        # fit has to refuse rather than silently pick the wrong turn.
        leader = [10.0, 350.0, 30.0, 330.0]
        arm = [10.0, 210.0, 30.0, 190.0]
        self.assertIn("error", fit_joint(leader, arm, 30.0, 0.05, 3.0))


class SessionTests(unittest.TestCase):
    def test_too_few_poses_is_refused(self):
        results, problems = fit_session(session()[:MIN_POSES - 1], 30.0, 0.05, 3.0)
        self.assertEqual(results, [])
        self.assertIn("at least", problems[0])

    def test_poses_without_arm_angles_are_refused(self):
        poses = session()
        for pose in poses:
            pose["arm_deg"] = None
        _, problems = fit_session(poses, 30.0, 0.05, 3.0)
        self.assertIn("--arm", problems[0])

    def test_every_joint_is_reported_even_when_some_fail(self):
        poses = session()
        for pose in poses:
            pose["continuous_deg"][2] = 106.0  # J3 held still
        results, problems = fit_session(poses, 30.0, 0.05, 3.0)
        self.assertEqual(len(results), 6)
        self.assertEqual(len(problems), 1)
        self.assertIn("J3:", problems[0])

    def test_build_map_and_the_loader_agree(self):
        poses = session()
        results, problems = fit_session(poses, 30.0, 0.05, 3.0)
        self.assertEqual(problems, [])
        mapping = check_map_loads(build_map(results, poses, "session.jsonl"))
        self.assertTrue(mapping.calibrated)
        self.assertEqual([joint.sign for joint in mapping.joints], [1.0] * 6)
        for joint, offset in zip(mapping.joints, OFFSETS):
            self.assertAlmostEqual(joint.offset_deg, offset, places=4)

    def test_the_map_reproduces_the_recorded_arm_angles(self):
        # The whole point: run a session's frames through the decoder's own
        # mapper and land on the arm angles that were recorded beside them.
        poses = session()
        results, _ = fit_session(poses, 30.0, 0.05, 3.0)
        mapper = Mapper(check_map_loads(build_map(results, poses, "session.jsonl")))
        for pose in poses:
            radians = mapper.to_radians(pose["raw_deg"])
            for produced, expected in zip(radians, pose["arm_deg"]):
                self.assertAlmostEqual(math.degrees(produced), expected, places=3)

    def test_the_map_reproduces_a_session_that_crosses_the_rollover(self):
        # J1 goes 350 -> 370, which the board reports as 350 -> 10. The arm
        # angles belong to the real (unwrapped) travel, so a fit that ignored
        # the rollover would be 360 degrees out on the second pose.
        continuous = [[350.0, 200.0, 100.0, 50.0, 300.0, 220.0],
                      [370.0, 220.0, 130.0, 20.0, 330.0, 250.0],
                      [320.0, 180.0, 60.0, 40.0, 280.0, 200.0]]
        poses = [{"raw_deg": [value % 360.0 for value in pose],
                  "continuous_deg": list(pose), "arm_deg": arm_for(pose)}
                 for pose in continuous]
        results, problems = fit_session(poses, 30.0, 0.05, 3.0)
        self.assertEqual(problems, [])
        mapper = Mapper(check_map_loads(build_map(results, poses, "session.jsonl")))
        for pose in poses:
            radians = mapper.to_radians(pose["raw_deg"])
            for produced, expected in zip(radians, pose["arm_deg"]):
                self.assertAlmostEqual(math.degrees(produced), expected, places=3)


class SummariseTests(unittest.TestCase):
    def test_the_median_ignores_a_flipped_byte_but_the_jitter_flags_it(self):
        # A single flipped byte is not repaired, it is outvoted: the median is
        # the estimate, and the jitter is what says the window was not clean.
        good = [(tuple([10.0] * 6), tuple([10.0] * 6))] * 9
        flipped = [(tuple([10.0] * 6), (10.0, 10.0, 250.0, 10.0, 10.0, 10.0))]
        pose = summarise(good + flipped, 0, None)
        self.assertAlmostEqual(pose["raw_deg"][2], 10.0)
        self.assertGreater(pose["jitter_deg"][2], JITTER_WARN_DEG)
        self.assertIn("moved", pose_problems(pose)[0])

    def test_jitter_reports_that_the_operator_did_not_hold_still(self):
        samples = [(tuple([10.0] * 6), (10.0 + step,) + tuple([10.0] * 5))
                   for step in (0.0, 2.0)]
        pose = summarise(samples, 0, None)
        self.assertAlmostEqual(pose["jitter_deg"][0], 2.0)
        self.assertIn("moved", pose_problems(pose)[0])

    def test_bad_frames_in_the_window_are_reported(self):
        pose = summarise([(tuple([1.0] * 6), tuple([1.0] * 6))], 3, None)
        self.assertIn("bad frame", pose_problems(pose)[0])


class LeastSquaresTests(unittest.TestCase):
    def test_a_flat_line_has_no_slope(self):
        self.assertEqual(least_squares([1.0, 1.0, 1.0], [2.0, 5.0, 9.0]),
                         (0.0, 16.0 / 3))

    def test_recovers_a_line(self):
        slope, intercept = least_squares([0.0, 1.0, 2.0], [3.0, 5.0, 7.0])
        self.assertAlmostEqual(slope, 2.0)
        self.assertAlmostEqual(intercept, 3.0)


class PseudoTerminalTests(unittest.TestCase):
    """A pty stands in for the leader board so the reading loop can be tested."""

    def setUp(self):
        self.master, self.slave = pty.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)

    def feed(self, payload):
        os.write(self.master, payload)

    def drain(self, window=0.05):
        slave = self.slave

        class Source:
            def read(self):
                if select.select([slave], [], [], 0)[0]:
                    return os.read(slave, 4096)
                return b""

        return collect(SamplingDecoder(), Source(), window)

    def test_collects_every_frame_of_a_steady_pose(self):
        self.feed(line(100, 200, 300, 400, 500, 600, 500) * 5)
        samples, errors = self.drain()
        self.assertEqual(errors, 0)
        self.assertEqual(len(samples), 5)
        self.assertEqual(samples[0][0], (10.0, 20.0, 30.0, 40.0, 50.0, 60.0))

    def test_a_garbled_frame_is_counted_without_dropping_the_pose(self):
        self.feed(line(100, 200, 300, 400, 500, 600, 500))
        self.feed(line(100, 200, 300, 400, 500, 600, 9999))
        self.feed(line(100, 200, 300, 400, 500, 600, 500))
        samples, errors = self.drain()
        self.assertEqual(errors, 1)
        self.assertEqual(len(samples), 2)

    def test_a_silent_port_yields_nothing(self):
        self.assertEqual(self.drain(), ([], 0))


class InteractiveTests(unittest.TestCase):
    """The capture loop, driven by a scripted keyboard and a clock the test owns."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.stream = io.StringIO()

    def build(self, script=(), payloads=(), arm=None, window=1.0, **kwargs):
        """A session wired to fakes. Time jumps 2 s per read, so a 1 s window
        holds exactly the payload just delivered and nothing before it."""
        self.clock = Clock()
        live = InteractiveSession(
            source=Feeder(payloads, self.clock, on_read=None if arm is None else arm.advance),
            arm=arm, keys=FakeKeys(script), stream=self.stream, window=window,
            session_path=kwargs.pop("session_path", self.root / "session.jsonl"),
            map_path=kwargs.pop("map_path", self.root / "leader_map.json"),
            clock=self.clock, sleep=lambda _: None,
            plain=kwargs.pop("plain", True), **kwargs)
        return live

    def test_a_capture_holds_the_pose_on_screen(self):
        live = self.build(script=["c"], payloads=[payload(LEADER_POSES[0])])
        live.step()
        self.assertEqual(len(live.poses), 1)
        self.assertEqual(live.poses[0]["frames"], MIN_FRAMES + 5)
        self.assertAlmostEqual(live.poses[0]["raw_deg"][0], 81.7)

    def test_the_arm_side_is_read_at_capture_time(self):
        arm = FakeArm([arm_for(LEADER_POSES[0])])
        live = self.build(script=["c"], payloads=[payload(LEADER_POSES[0])], arm=arm)
        live.step()
        for recorded, expected in zip(live.poses[0]["arm_deg"], arm_for(LEADER_POSES[0])):
            self.assertAlmostEqual(recorded, expected)

    def test_the_window_forgets_what_the_operator_has_moved_past(self):
        live = self.build(script=["c", "c"],
                          payloads=[payload(LEADER_POSES[0]), payload(LEADER_POSES[1])])
        live.step()
        live.step()
        # The second capture must be the second pose, not a blend of both.
        self.assertEqual(live.poses[1]["frames"], MIN_FRAMES + 5)
        self.assertAlmostEqual(live.poses[1]["raw_deg"][0], 140.2)

    def test_a_silent_leader_is_reported_instead_of_captured(self):
        live = self.build(script=["c"])
        live.step()
        self.assertEqual(live.poses, [])
        self.assertIn("leader frame", live.message)

    def test_an_arm_that_will_not_answer_keeps_the_pose_out(self):
        arm = FakeArm([arm_for(LEADER_POSES[0])])
        arm.error = RuntimeError("can0 is down")
        live = self.build(script=["c"], payloads=[payload(LEADER_POSES[0])], arm=arm)
        live.step()
        self.assertEqual(live.poses, [])
        self.assertIn("can0 is down", live.message)

    def test_an_operator_still_moving_is_warned_about(self):
        live = self.build(script=["c"], payloads=[payload(LEADER_POSES[0], 10)
                                                  + payload(LEADER_POSES[1], 15)])
        live.step()
        self.assertEqual(len(live.poses), 1)  # Warned, not refused: the fit decides.
        self.assertIn("moved", live.message)

    def test_a_pose_repeated_verbatim_is_called_out(self):
        live = self.build(script=["c", "c"],
                          payloads=[payload(LEADER_POSES[0]), payload(LEADER_POSES[0])])
        live.step()
        live.step()
        self.assertIn("nearly the same pose", live.message)

    def test_undo_drops_the_pose_just_captured(self):
        live = self.build(script=["c", "u"], payloads=[payload(LEADER_POSES[0])])
        live.step()
        live.step()
        self.assertEqual(live.poses, [])
        self.assertIn("dropped pose 1", live.message)

    def test_undo_with_nothing_captured_says_so(self):
        live = self.build(script=["u"])
        live.step()
        self.assertIn("nothing to undo", live.message)

    def test_the_readout_names_the_joints_that_still_need_moving(self):
        live = self.build()
        self.assertEqual(live.span_note(), "all six (no poses yet)")
        live = self.build(script=["c", "c"],
                          payloads=[payload(LEADER_POSES[0]), payload(LEADER_POSES[1])])
        live.step()
        live.step()
        # Every joint moved well past the minimum span between these two.
        self.assertEqual(live.span_note(), "none -- press f to fit")

    def test_the_readout_names_joints_that_never_moved(self):
        live = self.build(script=["c", "c"],
                          payloads=[payload(LEADER_POSES[0]), payload(LEADER_POSES[0])])
        live.step()
        live.step()
        for number in range(1, 7):
            self.assertIn(f"J{number}", live.span_note())

    def test_finishing_too_early_leaves_the_loop_running(self):
        live = self.build(script=["c", "f"], payloads=[payload(LEADER_POSES[0])])
        live.step()
        live.step()
        self.assertFalse(live.finished)
        self.assertFalse((self.root / "leader_map.json").exists())
        self.assertIn("pose", live.message)

    def test_finishing_without_an_arm_side_explains_what_is_missing(self):
        live = self.build(script=["c", "c", "c", "f"],
                          payloads=[payload(pose) for pose in LEADER_POSES[:3]])
        for _ in range(4):
            live.step()
        self.assertFalse(live.finished)
        self.assertIn("without arm angles", live.message)

    def test_a_full_run_writes_a_map_the_loader_accepts(self):
        arm = FakeArm([arm_for(pose) for pose in LEADER_POSES[:3]])
        live = self.build(script=["c", "c", "c", "f"],
                          payloads=[payload(pose) for pose in LEADER_POSES[:3]], arm=arm)
        self.assertEqual(live.run(), 0)
        mapping = load_mapping(self.root / "leader_map.json")
        self.assertTrue(mapping.calibrated)
        for index, offset in enumerate(OFFSETS):
            self.assertEqual(mapping.joints[index].sign, 1)
            self.assertAlmostEqual(mapping.joints[index].offset_deg, offset, places=3)
        # The reference pose has to be recoverable from the map, not just the numbers:
        # a teleop session that starts anywhere else shifts every target a whole turn.
        self.assertIn("81.7", (self.root / "leader_map.json").read_text(encoding="utf-8"))

    def test_quitting_partway_keeps_the_poses_and_says_a_map_is_missing(self):
        arm = FakeArm([arm_for(pose) for pose in LEADER_POSES[:3]])
        live = self.build(script=["c", "c", "c", "q"],
                          payloads=[payload(pose) for pose in LEADER_POSES[:3]], arm=arm)
        self.assertEqual(live.run(), 2)
        self.assertFalse((self.root / "leader_map.json").exists())
        poses = load_session(self.root / "session.jsonl")
        self.assertEqual(len(poses), 3)
        self.assertEqual(len(poses[0]["arm_deg"]), 6)
        # What was kept has to be what fit needs, or keeping it was pointless.
        self.assertEqual(fit_session(poses, 30.0, 0.05, 3.0)[1], [])

    def test_quitting_without_capturing_anything_is_not_a_failure(self):
        live = self.build(script=["q"])
        self.assertEqual(live.run(), 0)

    def test_the_live_readout_redraws_in_place(self):
        live = self.build(script=[], payloads=[payload(LEADER_POSES[0])], plain=False)
        live.step()
        live.step()
        drawn = self.stream.getvalue()
        self.assertIn("\x1b[", drawn)  # The cursor went back up over the first block.
        self.assertIn("still needing range", drawn)

    def test_help_lists_the_keys(self):
        live = self.build(script=["h"])
        live.step()
        self.assertIn("capture", live.message)

    def test_the_session_command_captures_from_a_terminal_and_a_port(self):
        """The whole command: a real pty keyboard, a real pty leader, no SDK."""
        console_master, console_slave = pty.openpty()
        leader_master, leader_slave = pty.openpty()
        for fd in (console_master, console_slave, leader_master, leader_slave):
            self.addCleanup(os.close, fd)
        stdin = os.fdopen(os.dup(console_slave), "r")
        self.addCleanup(stdin.close)
        # The session draws on the console descriptor it saved, not on sys.stdout,
        # so quieting the test run means moving fd 1 itself.
        quiet = os.open(os.devnull, os.O_WRONLY)
        saved_stdout = os.dup(1)
        os.dup2(quiet, 1)
        self.addCleanup(lambda: (os.dup2(saved_stdout, 1), os.close(saved_stdout),
                                 os.close(quiet)))

        def type_keys():
            os.write(console_master, b"c")  # Capture, then quit well after it.
            time.sleep(1.0)
            os.write(console_master, b"q")

        timer = threading.Timer(0.2, type_keys)
        self.addCleanup(timer.cancel)
        timer.start()
        leader = threading.Timer(0.1, os.write, (leader_master, payload(LEADER_POSES[0])))
        self.addCleanup(leader.cancel)
        leader.start()
        with mock.patch("sys.stdin", stdin):
            code = main(["session", "--serial", os.ttyname(leader_slave),
                         "--out", str(self.root / "session.jsonl"),
                         "--map", str(self.root / "leader_map.json"),
                         "--arm-log", str(self.root / "arm.log"), "--plain"])
        # Poses were kept, but with no arm side there is nothing to fit: exit 2.
        self.assertEqual(code, 2)
        self.assertFalse((self.root / "leader_map.json").exists())
        poses = load_session(self.root / "session.jsonl")
        self.assertEqual(len(poses), 1)
        self.assertAlmostEqual(poses[0]["raw_deg"][0], 81.7)
        # Nothing to log: without --arm the vendor library is never loaded.
        self.assertEqual((self.root / "arm.log").read_bytes(), b"")

    def test_the_arm_holds_through_the_session_and_is_released_on_confirmation(self):
        """--arm means gravity compensation, and SOFT comes back only on a keypress."""
        console_master, console_slave = pty.openpty()
        leader_master, leader_slave = pty.openpty()
        for fd in (console_master, console_slave, leader_master, leader_slave):
            self.addCleanup(os.close, fd)
        stdin = os.fdopen(os.dup(console_slave), "r")
        self.addCleanup(stdin.close)
        quiet = os.open(os.devnull, os.O_WRONLY)
        saved_stdout = os.dup(1)
        os.dup2(quiet, 1)
        self.addCleanup(lambda: (os.dup2(saved_stdout, 1), os.close(saved_stdout),
                                 os.close(quiet)))

        patcher = mock.patch("backends.VendorArm")
        self.addCleanup(patcher.stop)
        vendor = patcher.start()
        vendor.return_value.read_joints.return_value = (0.0,) * 6

        def type_keys():
            # Spaced far enough apart that each lands in its own poll: "\r" inside
            # a live session would be a capture, not a confirmation.
            os.write(console_master, b"c")
            time.sleep(1.0)
            os.write(console_master, b"q")
            time.sleep(1.0)
            os.write(console_master, b"\r")  # Now it means "let go".

        timer = threading.Timer(0.2, type_keys)
        self.addCleanup(timer.cancel)
        timer.start()
        leader = threading.Timer(0.1, os.write, (leader_master, payload(LEADER_POSES[0])))
        self.addCleanup(leader.cancel)
        leader.start()
        with mock.patch("sys.stdin", stdin):
            code = main(["session", "--serial", os.ttyname(leader_slave),
                         "--arm", "--model", "2023",
                         "--out", str(self.root / "session.jsonl"),
                         "--map", str(self.root / "leader_map.json"),
                         "--arm-log", str(self.root / "arm.log"), "--plain"])
        self.assertEqual(code, 2)
        vendor.return_value.enable_gravity_compensation.assert_called_once_with()
        # stop() is the confirmation path; close() still runs afterwards as the
        # unconditional backstop, and both end at SOFT.
        vendor.return_value.stop.assert_called_once_with()
        vendor.return_value.close.assert_called_once_with()
        self.assertEqual(len(load_session(self.root / "session.jsonl")), 1)


class ReleaseTests(unittest.TestCase):
    """Handing the arm back to SOFT is a question, not a side effect of exiting."""

    def setUp(self):
        self.arm = mock.Mock()
        self.console = io.StringIO()

    def release(self, keys):
        return confirm_release(self.arm, keys, self.console, sleep=lambda _: None)

    def test_the_arm_holds_until_the_operator_confirms(self):
        self.assertTrue(self.release(FakeKeys(["\r"])))
        self.arm.stop.assert_called_once_with()
        self.assertIn("GRAVITY COMPENSATION", self.console.getvalue())
        self.assertIn("SOFT", self.console.getvalue())

    def test_silence_is_not_a_confirmation(self):
        # Nothing to read yet must not be mistaken for a keypress.
        self.assertTrue(self.release(FakeKeys(["", "", "g"])))
        self.arm.stop.assert_called_once_with()

    def test_a_closed_stdin_still_returns_the_arm_to_soft(self):
        # The terminal went away; leaving the arm driven is the worse option.
        keys = FakeKeys([])
        keys.exhausted = True
        self.assertFalse(self.release(keys))
        self.arm.stop.assert_called_once_with()
        self.assertIn("stdin closed", self.console.getvalue())


class SignalTests(unittest.TestCase):
    """SIGTERM must not skip the cleanup that hands a driven arm back to SOFT."""

    def test_sigterm_becomes_an_interrupt(self):
        @treat_sigterm_as_interrupt
        def dying():
            os.kill(os.getpid(), signal.SIGTERM)
            return "not reached"

        with self.assertRaises(KeyboardInterrupt):
            dying()

    def test_the_previous_handler_is_restored(self):
        before = signal.getsignal(signal.SIGTERM)

        @treat_sigterm_as_interrupt
        def handler_while_running():
            return signal.getsignal(signal.SIGTERM)

        installed = handler_while_running()
        self.assertIsNot(installed, before)
        self.assertIs(signal.getsignal(signal.SIGTERM), before)


class VendorChatterTests(unittest.TestCase):
    """The vendor SDK prints from C++, so fd 1 has to move for real."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.log = Path(directory.name) / "arm.log"

    def test_what_the_sdk_prints_lands_in_the_log_not_on_the_console(self):
        with VendorChatter(self.log):
            os.write(1, b"vendor says hello\n")
            os.write(2, b"vendor says oops\n")
        written = self.log.read_bytes()
        self.assertIn(b"vendor says hello", written)
        self.assertIn(b"vendor says oops", written)

    def test_the_console_descriptors_come_back_unharmed(self):
        before = os.fstat(1), os.fstat(2)
        with VendorChatter(self.log):
            self.assertNotEqual(os.fstat(1).st_ino, before[0].st_ino)
            self.assertNotEqual(os.fstat(2).st_ino, before[1].st_ino)
        # Including stderr: it is usually the same terminal, but restoring it
        # from the descriptor that replaced stdout would lose a redirected one.
        self.assertEqual(os.fstat(1).st_ino, before[0].st_ino)
        self.assertEqual(os.fstat(2).st_ino, before[1].st_ino)
        self.assertEqual(os.fstat(2).st_dev, before[1].st_dev)

    def test_the_console_is_writable_while_redirected(self):
        with VendorChatter(self.log) as console:
            console.write("")
            self.assertTrue(console.writable())


class CommandTests(unittest.TestCase):
    """The CLI surface, including the paths that must refuse."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.session = Path(directory.name) / "session.jsonl"
        self.out = Path(directory.name) / "leader_map.json"

    def send_after_open(self, master, payload, delay=0.1):
        """Write once sample() has opened the port.

        SerialInput flushes the input buffer on open, so anything written before
        that is discarded -- as it would be for a real board already streaming.
        """
        timer = threading.Timer(delay, os.write, (master, payload))
        self.addCleanup(timer.cancel)
        timer.start()

    def write_session(self, poses):
        with open(self.session, "w", encoding="utf-8") as stream:
            for pose in poses:
                stream.write(json.dumps(pose) + "\n")

    def test_fit_writes_a_loadable_map(self):
        self.write_session(session())
        self.assertEqual(main(["fit", str(self.session), "--out", str(self.out)]), 0)
        self.assertTrue(load_mapping(self.out).calibrated)

    def test_fit_refuses_and_writes_nothing_when_a_joint_fails(self):
        poses = session()
        for pose in poses:
            pose["continuous_deg"][4] = 299.3  # J5 never moved
        self.write_session(poses)
        self.assertEqual(main(["fit", str(self.session), "--out", str(self.out)]), 2)
        self.assertFalse(self.out.exists())

    def test_fit_refuses_a_session_without_arm_angles(self):
        poses = session()
        for pose in poses:
            pose["arm_deg"] = None
        self.write_session(poses)
        self.assertEqual(main(["fit", str(self.session)]), 2)

    def test_a_missing_session_is_an_error_not_a_traceback(self):
        self.assertEqual(main(["fit", str(self.session)]), 2)

    def test_an_unreadable_pose_names_its_line(self):
        self.write_session(session())
        with open(self.session, "a", encoding="utf-8") as stream:
            stream.write("{not json}\n")
        self.assertEqual(main(["fit", str(self.session)]), 2)

    def test_the_interactive_session_needs_a_terminal(self):
        # Refused before the port is opened or the SDK is loaded, not after.
        with mock.patch("sys.stdin", io.StringIO("")):
            self.assertEqual(main(["session", "--serial", "/dev/null"]), 2)

    def test_sample_needs_a_model_before_touching_the_arm(self):
        self.assertEqual(main(["sample", "--serial", "/dev/null", "--arm"]), 2)

    def test_sample_reports_a_dead_port_without_writing_a_pose(self):
        self.assertEqual(main(["sample", "--serial", "/dev/null", "--out",
                               str(self.session), "--window", "0.05"]), 2)
        self.assertFalse(self.session.exists())

    def test_sample_records_a_pose(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        payload = line(81, 19, 106, 256, 299, 201, 500) * 40
        self.send_after_open(master, payload)
        self.assertEqual(main(["sample", "--serial", os.ttyname(slave),
                               "--out", str(self.session), "--window", "0.4",
                               "--label", "home"]), 0)
        poses = load_session(self.session)
        self.assertEqual(len(poses), 1)
        self.assertEqual(poses[0]["label"], "home")
        self.assertIsNone(poses[0]["arm_deg"])
        self.assertAlmostEqual(poses[0]["raw_deg"][0], 8.1)

    def test_sample_with_arm_holds_then_hands_the_arm_back(self):
        vendor = self.patched_arm()
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        self.send_after_open(master, line(81, 19, 106, 256, 299, 201, 500) * 40)
        self.assertEqual(main(["sample", "--serial", os.ttyname(slave),
                               "--out", str(self.session), "--window", "0.4",
                               "--arm", "--model", "2023"]), 0)
        # Order matters: the arm must be holding the pose before it is read, and
        # must be back in SOFT before this process goes away.
        self.assertEqual([call[0] for call in vendor.return_value.method_calls],
                         ["enable_gravity_compensation", "read_joints", "close"])

    def test_sample_without_arm_never_constructs_the_sdk(self):
        vendor = self.patched_arm()
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        self.send_after_open(master, line(81, 19, 106, 256, 299, 201, 500) * 40)
        self.assertEqual(main(["sample", "--serial", os.ttyname(slave),
                               "--out", str(self.session), "--window", "0.4"]), 0)
        vendor.assert_not_called()

    def test_an_interrupt_hands_the_arm_back_without_asking(self):
        """Ctrl-C wants out now, so the release prompt must not run."""
        vendor = self.patched_arm()
        _, leader_slave, stdin = self.terminal()
        with mock.patch("sys.stdin", stdin):
            with mock.patch("leader_calibrate.InteractiveSession") as live:
                live.return_value.run.side_effect = KeyboardInterrupt
                code = main(["session", "--serial", os.ttyname(leader_slave),
                             "--arm", "--model", "2023",
                             "--out", str(self.session),
                             "--map", str(self.out),
                             "--arm-log", str(self.out.parent / "arm.log"), "--plain"])
        self.assertEqual(code, 130)
        vendor.return_value.enable_gravity_compensation.assert_called_once_with()
        # stop() is what confirm_release would have sent; close() is the belt-and-braces
        # release in the finally, and it always has to happen.
        vendor.return_value.stop.assert_not_called()
        vendor.return_value.close.assert_called_once_with()

    def patched_arm(self):
        """A vendor SDK that records the arm states it was asked for."""
        patcher = mock.patch("backends.VendorArm")
        self.addCleanup(patcher.stop)
        vendor = patcher.start()
        vendor.return_value.read_joints.return_value = (0.0,) * 6
        return vendor

    def terminal(self):
        """A pty for the keyboard, a pty for the leader, and fd 1 quieted.

        session() refuses to start without a tty and draws on the descriptor it
        saved from fd 1, so both have to be real file descriptors.
        """
        console_master, console_slave = pty.openpty()
        leader_master, leader_slave = pty.openpty()
        for fd in (console_master, console_slave, leader_master, leader_slave):
            self.addCleanup(os.close, fd)
        quiet = os.open(os.devnull, os.O_WRONLY)
        saved = os.dup(1)
        os.dup2(quiet, 1)
        self.addCleanup(lambda: (os.dup2(saved, 1), os.close(saved), os.close(quiet)))
        stdin = os.fdopen(os.dup(console_slave), "r")
        self.addCleanup(stdin.close)
        return console_master, leader_slave, stdin

    def test_a_second_sample_appends_rather_than_replaces(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        payload = line(81, 19, 106, 256, 299, 201, 500) * 40
        for _ in range(2):
            self.send_after_open(master, payload)
            self.assertEqual(main(["sample", "--serial", os.ttyname(slave),
                                   "--out", str(self.session), "--window", "0.4"]), 0)
        self.assertEqual(len(load_session(self.session)), 2)


if __name__ == "__main__":
    unittest.main()
