"""Drive the leader decoder end to end on a pseudo terminal, with a mock arm.

Nothing here opens CAN or constructs the vendor SDK: the point is that the
whole path -- serial bytes, decoder, mapping, operator keys, state machine --
works together before any of it is pointed at real motors.
"""

import json
import math
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest

PROJECT = Path(__file__).resolve().parents[1]
APP = PROJECT / "app.py"
DECODER = PROJECT / "leader_decoder.py"

CAPTURED = b"795,3281,1060,2353,2875,2085,500"
HANDSHAKE = b"0123456789"
NO_DATA = b"-1,3281,1060,2353,2875,2085,500"
# CAPTURED in degrees, which is how a map records the pose it was measured at.
REFERENCE = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]

WIDE_LIMITS = {"lower": [-6.3] * 6, "upper": [6.3] * 6,
               "max_speed": 2.0, "max_following_error": 0.5, "timeout": 0.25}


def leader_frame(record):
    """The leader's last frame, or an empty dict while there is none yet.

    The telemetry block is present as soon as the first report is printed but
    the frame inside it starts as None, so every read of it has to get past
    that before touching a field.
    """
    return (record.get("leader") or {}).get("frame") or {}


def mapping_from(reference, inverted=(0,)):
    """A map that puts the mock arm's rest pose (all zeroes) at ``reference``.

    Arming now requires the leader and the arm to be in the same pose, and the
    mock arm never moves on its own, so the map has to be built around its
    zero: with ``needed = (arm_deg - offset) / sign`` and the arm at zero, the
    offset that makes the leader's reference angles come out is ``-sign * angle``.

    A few joints are inverted, so a passing test proves the mapping is applied
    and not just that the raw degrees round-tripped.
    """
    joints = []
    for index, angle in enumerate(reference):
        sign = -1 if index in inverted else 1
        joints.append({"sign": sign, "offset_deg": -sign * angle, "unwrap": True})
    return {"calibrated": True, "joints": joints}


class LeaderHarness(unittest.TestCase):
    """Runs the app on a pty with a mock arm. Holds no tests of its own.

    The map decides which pose the arm and the leader have to share, so the
    groups below share this and differ only in ``mapping_config``.
    """

    PRINT_RATE = "100"
    EXTRA_ARGS = ()
    LIMITS = WIDE_LIMITS

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        mapping = Path(self.directory.name) / "leader_map.json"
        mapping.write_text(json.dumps(self.mapping_config()), encoding="utf-8")
        limits = Path(self.directory.name) / "limits.json"
        limits.write_text(json.dumps(self.LIMITS), encoding="utf-8")

        self.master, self.slave = pty.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        environment = dict(os.environ)
        environment.pop("ARX_LEADER_MAP", None)
        self.process = subprocess.Popen(
            [sys.executable, "-u", str(APP), "--mode", "teleop", "--backend", "mock",
             "--serial", os.ttyname(self.slave), "--decoder", str(DECODER),
             "--leader-map", str(mapping), "--operator-keys", "--limits", str(limits),
             "--rate", "100", "--print-rate", self.PRINT_RATE, *self.EXTRA_ARGS],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=environment,
        )
        self.addCleanup(self.stop_process)
        self.buffer = b""
        self.records = []
        self.lines = []
        # Any line, whichever framing this mode prints: what is being waited for
        # is that the readout has started, and the per-test waits do the rest.
        self.wait_for_text("")

    def mapping_config(self):
        return mapping_from(REFERENCE)

    def stop_process(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        for stream in (self.process.stdout, self.process.stderr, self.process.stdin):
            stream.close()

    def send(self, payload):
        os.write(self.master, payload + b"\r\n")

    def press(self, keys):
        self.process.stdin.write(keys)
        self.process.stdin.flush()

    def press_arm(self, stream=CAPTURED):
        """Arm the way an operator can: only after a live frame has been seen.

        The decoder's unwrap origin is the first frame it sees, so arming before
        any frame has arrived is refused rather than allowed to race the stream.
        """
        self.wait_for(lambda r: r.get("leader", {}).get("frame"), stream)
        self.press(b"a")

    def wait_for_text(self, fragment, stream=b"", timeout=5):
        """Wait for a raw line containing `fragment`, for the text readout.

        The record waits above parse JSON, which --watch does not print; this
        one only looks at the line, so it also serves as "wait for any output".
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                text = line.decode("utf-8", "replace")
                self.lines.append(text)
                if fragment in text:
                    return text
            if stream:
                self.send(stream)
            if select.select([self.process.stdout], [], [], 0.02)[0]:
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.fail(f"app exited early: {self.process.stderr.read().decode()}")
                self.buffer += chunk
        self.fail(f"No line matching {fragment!r}. Last lines: {self.lines[-3:]}")

    def wait_for(self, predicate, stream=b"", timeout=5):
        """Wait for a status line, re-sending `stream` each round when given.

        Frames have to keep arriving or the 0.25 s command watchdog fires.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                record = json.loads(line)
                self.records.append(record)
                if predicate(record):
                    return record
            if stream:
                self.send(stream)
            if select.select([self.process.stdout], [], [], 0.02)[0]:
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.fail(f"app exited early: {self.process.stderr.read().decode()}")
                self.buffer += chunk
        self.fail(f"No matching status. Last records: {self.records[-3:]}")

class LeaderIntegrationTests(LeaderHarness):
    """The state machine and the decoder, on a map with no reference pose."""

    def test_stream_is_decoded_and_reported_while_stopped(self):
        self.send(HANDSHAKE)
        self.send(CAPTURED)
        record = self.wait_for(lambda r: r.get("leader", {}).get("frame"), CAPTURED)
        frame = record["leader"]["frame"]
        self.assertEqual(frame["fields"], [795, 3281, 1060, 2353, 2875, 2085, 500])
        self.assertAlmostEqual(frame["angle_deg"][0], 79.5)
        self.assertEqual(frame["gripper"], 500)
        self.assertTrue(record["leader"]["calibrated"])
        self.assertEqual(record["state"], "STOPPED")  # nobody armed it

    def test_handshake_alone_never_faults(self):
        self.send(HANDSHAKE)
        record = self.wait_for(lambda r: r.get("leader", {}).get("resets", 0) >= 1)
        self.assertNotIn("error", record["leader"])

    def test_local_key_arms_and_the_mapping_reaches_the_mock_arm(self):
        self.press_arm()
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)
        # J1 is inverted by the map, so a leader angle above the arm's own pose
        # has to come out as a negative target and the arm has to follow it
        # down. The arm sits at the reference, so nudging the leader up is what
        # makes the direction visible.
        nudged = b"800,3281,1060,2353,2875,2085,500"
        moving = self.wait_for(lambda r: r["joints_rad"][0] < 0, nudged)
        self.assertEqual(moving["state"], "ACTIVE")
        self.assertLess(moving["leader"]["frame"]["target_rad"][0], 0)
        self.assertAlmostEqual(moving["leader"]["frame"]["angle_deg"][0], 80.0)

    def test_arming_before_the_leader_says_anything_is_refused(self):
        # There is no origin to judge yet, and the first key press must not be a
        # race the gate loses.
        self.press(b"a")
        record = self.wait_for(lambda r: "refusing to arm" in r["reason"])
        self.assertEqual(record["state"], "STOPPED")

    def test_local_key_stops(self):
        self.press_arm()
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)
        self.press(b"s")
        self.wait_for(lambda r: r["state"] == "STOPPED", CAPTURED)

    def test_no_data_after_a_valid_frame_latches_a_fault(self):
        self.wait_for(lambda r: r.get("leader", {}).get("frame"), CAPTURED)
        record = self.wait_for(lambda r: r["state"] == "FAULT", NO_DATA)
        self.assertIn("no data", record["reason"])

    def test_no_data_frame_alone_is_a_startup_transient_not_a_fault(self):
        record = self.wait_for(lambda r: r.get("leader", {}).get("no_data"), NO_DATA)
        self.assertEqual(record["state"], "STOPPED")
        self.assertNotIn("error", record["leader"])

    def test_out_of_range_field_is_reported_as_a_fault(self):
        poisoned = b"795,3281,1060,2353,2875,2085,1001"
        record = self.wait_for(lambda r: r["state"] == "FAULT", poisoned)
        self.assertIn("gripper field 1001", record["reason"])
        self.assertIn("gripper field 1001", record["leader"]["error"])

    def test_recovery_needs_a_stop_then_an_arm(self):
        self.press_arm()
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)
        self.wait_for(lambda r: r["state"] == "FAULT", b"795,3281,1060,2353,2875,2085,1001")
        self.press(b"a")  # refused while latched
        self.wait_for(lambda r: r["state"] == "FAULT", CAPTURED)
        self.press(b"s")
        self.wait_for(lambda r: r["state"] == "STOPPED", CAPTURED)
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)

    def test_clean_shutdown(self):
        self.process.send_signal(signal.SIGINT)
        self.wait_for(lambda r: r["reason"] == "program exit")
        self.assertEqual(self.process.wait(timeout=3), 0)


class MatchedPoseTests(LeaderHarness):
    """The leader is in the pose the arm is in, so arming is allowed.

    The map is the one above, which puts the mock arm's rest pose at CAPTURED,
    so nothing has to move for the two to agree.
    """

    def test_the_leader_in_the_arm_s_pose_is_allowed_to_arm(self):
        self.press_arm()
        record = self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)
        self.assertTrue(record["leader"]["anchor"]["ok"])
        self.assertEqual(record["leader"]["anchor"]["turns_deg"], [0.0] * 6)

    def test_a_hand_placement_error_within_the_tolerance_is_allowed(self):
        # Half a degree is as close as a hand gets, and the residual it leaves
        # is what the arm walks to meet the leader -- which is the whole point
        # of the tolerance being a walk and not a jump.
        nudged = b"800,3281,1060,2353,2875,2085,500"  # J1 0.5 deg up
        self.press_arm(nudged)
        record = self.wait_for(lambda r: r["state"] == "ACTIVE", nudged)
        self.assertAlmostEqual(record["leader"]["anchor"]["residual_deg"][0], 0.5)

    def test_arming_before_the_leader_says_anything_is_refused(self):
        self.press(b"a")
        record = self.wait_for(lambda r: "refusing to arm" in r["reason"])
        self.assertEqual(record["state"], "STOPPED")


class MismatchedPoseTests(LeaderHarness):
    """Same map, but the leader is a quarter turn away from where the arm is."""

    AWAY = b"795,3281,1960,2353,2875,2085,500"  # J3 reads 196 where the arm is at 106

    def test_arming_is_refused_and_the_reason_says_which_joint(self):
        self.press_arm(self.AWAY)
        record = self.wait_for(lambda r: "refusing to arm" in r["reason"], self.AWAY)
        self.assertEqual(record["state"], "STOPPED")
        self.assertIn("J3", record["reason"])
        self.assertFalse(record["leader"]["anchor"]["ok"])
        self.assertEqual(record["leader"]["anchor"]["worst_joint"], 2)

    def test_the_arm_is_never_commanded(self):
        self.press_arm(self.AWAY)
        self.wait_for(lambda r: "refusing to arm" in r["reason"], self.AWAY)
        # Stopped is not enough on its own: nothing may have been written, and
        # the mock arm starts from zero like the leader's own zero would.
        self.assertTrue(all(abs(q) < 1e-9 for r in self.records
                            for q in r.get("joints_rad", [])))

    def test_moving_the_leader_to_the_arm_and_pressing_again_arms(self):
        # Nothing is latched: the operator lines the two up and tries again.
        self.press_arm(self.AWAY)
        self.wait_for(lambda r: "refusing to arm" in r["reason"], self.AWAY)
        self.wait_for(lambda r: leader_frame(r).get("angle_deg", [None] * 3)[2] == 106.0,
                      CAPTURED)
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)


class PrintRateTests(LeaderHarness):
    """A rate low enough to read has to actually be low.

    The loop runs at 100 Hz and the readout is on its own timer, so the two are
    easy to conflate at the call site -- and the whole point of turning the rate
    down is that a person can read the line.
    """

    PRINT_RATE = "1"

    def test_the_readout_keeps_to_the_print_rate_not_the_control_loop(self):
        # ~2 s of streaming, so a rate of 1 Hz owes a couple of lines and the
        # control loop would have produced a couple of hundred.
        self.wait_for(lambda r: r.get("leader", {}).get("frames", 0) >= 60, CAPTURED)
        self.assertLess(len(self.records), 6)


class WatchModeTests(LeaderHarness):
    """``--watch`` prints the line a person reads instead of the JSON record.

    It has to be the same measurement as the gate, or the operator would be
    watching one number and refused by another.
    """

    EXTRA_ARGS = ("--watch",)

    def test_the_readout_is_a_line_and_not_a_record(self):
        line = self.wait_for_text("J1", CAPTURED)
        self.assertRegex(line, r"^\d\d:\d\d:\d\d STOPPED")
        self.assertNotIn("{", line)
        self.assertIn("J6", line)

    def test_it_says_when_pressing_a_would_work(self):
        # The harness map puts the arm's rest pose at CAPTURED, so a leader in
        # that pose reads as zero on every joint.
        self.assertIn("in the arm's pose, press a",
                      self.wait_for_text("in the arm's pose", CAPTURED))

    def test_it_names_the_joints_that_are_out(self):
        # J3 reads 196 where the arm's pose calls for 106: a quarter turn out,
        # and the reason this line exists is to be watched on the way to zero.
        away = b"795,3281,1960,2353,2875,2085,500"
        line = self.wait_for_text("out of pose", away)
        self.assertIn("J3", line)
        self.assertIn("-90.0", line)

    def test_before_a_frame_it_says_it_is_waiting(self):
        self.assertIn("waiting for the leader's first frame", self.wait_for_text("waiting"))

    def test_pressing_a_is_reported_on_the_following_line(self):
        self.wait_for_text("in the arm's pose", CAPTURED)
        self.press(b"a")
        line = self.wait_for_text("ACTIVE", CAPTURED)
        self.assertIn("armed at measured position", line)


class RolloverTests(LeaderHarness):
    """The encoder's 0/360 seam, and the whole-turn bias that exists for it.

    The arm's pose corresponds to a leader angle of 354.0 on J1 while the leader
    reads 4.0: ten degrees apart, but on opposite sides of the seam. Before the
    bias this session was refused outright as -350 degrees out.
    """

    BEFORE = [354.0, 328.1, 106.0, 235.3, 287.5, 208.5]
    AFTER = b"40,3281,1060,2353,2875,2085,500"
    NEXT = b"50,3281,1060,2353,2875,2085,500"

    def mapping_config(self):
        return mapping_from(self.BEFORE)

    def test_a_leader_just_past_the_seam_arms_against_an_arm_just_before_it(self):
        self.press_arm(self.AFTER)
        record = self.wait_for(lambda r: r["state"] == "ACTIVE", self.AFTER)
        anchor = record["leader"]["anchor"]
        self.assertTrue(anchor["ok"])
        self.assertEqual(anchor["turns_deg"][0], 360.0)
        self.assertAlmostEqual(anchor["residual_deg"][0], 10.0)

    def test_the_mapping_keeps_going_instead_of_jumping_back_a_turn(self):
        # 4.0 then 5.0 has to map to 364 then 365, so the arm follows the hand
        # down past the seam rather than being sent back to 4.
        self.press_arm(self.AFTER)
        self.wait_for(lambda r: r["state"] == "ACTIVE", self.AFTER)
        record = self.wait_for(
            lambda r: leader_frame(r).get("angle_deg", [None])[0] == 5.0, self.NEXT)
        # 365 on this inverted joint is -11 deg, which is where the arm is now
        # heading -- the other side of the seam, the way the hand moved.
        self.assertAlmostEqual(record["leader"]["frame"]["target_rad"][0],
                               math.radians(-11.0))
        self.wait_for(lambda r: r["joints_rad"][0] < -0.19, self.NEXT)


class PushedPastAJointBound:
    """One joint's worth of evidence that an out-of-range input does not end a run.

    The shared map is built for the mock arm's rest pose, so the arm sits at zero
    and the leader's own J1 is inverted: a leader reading 75.5 where that pose
    calls for 79.5 asks the arm's J1 for +4.0 deg. The configured upper bound
    here is +0.05 rad (2.9 deg), and every other joint is left exactly where the
    arm already is, so the clamp is about J1 alone.
    """

    LIMITS = dict(WIDE_LIMITS, upper=[0.05] + [6.3] * 5)
    NUDGED = b"755,3281,1060,2353,2875,2085,500"


class ClampedTargetTests(PushedPastAJointBound, LeaderHarness):
    def test_the_run_continues_and_the_arm_stops_at_the_bound(self):
        self.press_arm()
        self.wait_for(lambda r: r["state"] == "ACTIVE", CAPTURED)
        record = self.wait_for(lambda r: r["joints_rad"][0] > 0.04, self.NUDGED)
        # Not stopped and not faulted: the arm is where the bound is, holding,
        # and the leader is still being read -- the run is intact.
        self.assertEqual(record["state"], "ACTIVE")
        self.assertLessEqual(record["joints_rad"][0], 0.05)
        # Only the command was clamped. The decoder still resolved the leader's
        # own angle, and it is past the bound -- which is the thing that would
        # have ended the session before.
        self.assertGreater(record["leader"]["frame"]["target_rad"][0], 0.05)


class ClampedWatchLineTests(PushedPastAJointBound, LeaderHarness):
    """The line has to say the arm is held, or it reads as merely slow."""

    EXTRA_ARGS = ("--watch",)

    def test_the_line_names_the_joint_held_at_its_bound(self):
        # Armed through the text readout, the way an operator does it in this
        # mode: the record waits above never see JSON here.
        self.wait_for_text("in the arm's pose, press a", CAPTURED)
        self.press(b"a")
        line = self.wait_for_text("at the limit: J1", self.NUDGED)
        self.assertIn("ACTIVE", line)
        self.assertIn("armed at measured position", line)


if __name__ == "__main__":
    unittest.main()
