import json
import math
import os
from pathlib import Path
import pty
import select
import tempfile
import threading
import unittest

from leader_calibrate import (
    JITTER_WARN_DEG, MIN_POSES, SamplingDecoder, build_map, check_map_loads, collect, fit_joint,
    fit_session, least_squares, load_session, main, pose_problems, summarise,
    unwrap_from_reference,
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
