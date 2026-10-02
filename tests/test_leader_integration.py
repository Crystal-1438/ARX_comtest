"""Drive the leader decoder end to end on a pseudo terminal, with a mock arm.

Nothing here opens CAN or constructs the vendor SDK: the point is that the
whole path -- serial bytes, decoder, mapping, operator keys, state machine --
works together before any of it is pointed at real motors.
"""

import json
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

WIDE_LIMITS = {"lower": [-6.3] * 6, "upper": [6.3] * 6,
               "max_speed": 2.0, "max_following_error": 0.5, "timeout": 0.25}


class LeaderIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        mapping = Path(self.directory.name) / "leader_map.json"
        # J1 inverted, so a passing test proves the mapping is applied and not
        # just that the raw degrees round-tripped.
        mapping.write_text(json.dumps({
            "calibrated": True,
            "joints": [{"sign": -1, "offset_deg": 0.0, "unwrap": True}] +
                      [{"sign": 1, "offset_deg": 0.0, "unwrap": True}] * 5,
        }), encoding="utf-8")
        limits = Path(self.directory.name) / "limits.json"
        limits.write_text(json.dumps(WIDE_LIMITS), encoding="utf-8")

        self.master, self.slave = pty.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        environment = dict(os.environ)
        environment.pop("ARX_LEADER_MAP", None)
        self.process = subprocess.Popen(
            [sys.executable, "-u", str(APP), "--mode", "teleop", "--backend", "mock",
             "--serial", os.ttyname(self.slave), "--decoder", str(DECODER),
             "--leader-map", str(mapping), "--operator-keys", "--limits", str(limits),
             "--rate", "100", "--print-rate", "100"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=environment,
        )
        self.addCleanup(self.stop_process)
        self.buffer = b""
        self.records = []
        self.wait_for(lambda r: r["state"] == "STOPPED")

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
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        # J1 is inverted by the map, so both the decoded target and the arm
        # the mock reports must be negative.
        moving = self.wait_for(lambda r: r["joints_rad"][0] < 0, CAPTURED)
        self.assertEqual(moving["state"], "ACTIVE")
        self.assertLess(moving["leader"]["frame"]["target_rad"][0], 0)
        self.assertAlmostEqual(moving["leader"]["frame"]["angle_deg"][0], 79.5)

    def test_local_key_stops(self):
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        self.press(b"s")
        self.wait_for(lambda r: r["state"] == "STOPPED")

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
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        self.wait_for(lambda r: r["state"] == "FAULT", b"795,3281,1060,2353,2875,2085,1001")
        self.press(b"a")  # refused while latched
        self.wait_for(lambda r: r["state"] == "FAULT", CAPTURED)
        self.press(b"s")
        self.wait_for(lambda r: r["state"] == "STOPPED")
        self.press(b"a")
        self.wait_for(lambda r: r["state"] == "ACTIVE")

    def test_clean_shutdown(self):
        self.process.send_signal(signal.SIGINT)
        self.wait_for(lambda r: r["reason"] == "program exit")
        self.assertEqual(self.process.wait(timeout=3), 0)


if __name__ == "__main__":
    unittest.main()
