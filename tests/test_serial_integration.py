"""Exercise real pyserial on a pseudo terminal without CAN or robot hardware."""

import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import time
import unittest

APP = Path(__file__).resolve().parents[1] / "app.py"


@unittest.skipUnless(importlib.util.find_spec("serial"), "requires pyserial")
class SerialIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = pty.openpty()
        self.process = subprocess.Popen(
            [sys.executable, "-u", str(APP), "--mode", "teleop", "--backend", "mock",
             "--serial", os.ttyname(self.slave), "--print-rate", "100"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.buffer = b""
        self.records = []
        self.wait_for(lambda r: r["state"] == "STOPPED")

    def tearDown(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        self.process.stdout.close()
        self.process.stderr.close()
        os.close(self.master)
        os.close(self.slave)

    def send(self, seq, kind, **values):
        os.write(self.master, (json.dumps({"v": 1, "seq": seq, "type": kind, **values}) + "\n").encode())

    def wait_for(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                record = json.loads(line)
                self.records.append(record)
                if predicate(record):
                    return record
            if select.select([self.process.stdout], [], [], 0.05)[0]:
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.fail(f"app exited early: {self.process.stderr.read().decode()}")
                self.buffer += chunk
        self.fail(f"No matching status. Last records: {self.records[-3:]}")

    def test_split_frame_control_timeout_and_recovery(self):
        os.write(self.master, b'{"v":1,"seq":1,"type":"arm",')
        os.write(self.master, b'"deadman":true}\n')
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        self.send(2, "target", deadman=True, joints=[0.05] * 6)
        moving = self.wait_for(lambda r: r["joints_rad"][0] > 0)
        self.assertLess(moving["joints_rad"][0], 0.05)
        stopped = self.wait_for(lambda r: r["state"] == "FAULT")
        self.assertEqual(stopped["reason"], "serial command timeout")
        self.send(3, "arm", deadman=True)
        self.send(4, "target", deadman=True, joints=[0.1] * 6)
        self.wait_for(lambda r: r["state"] == "FAULT")
        self.send(5, "stop")
        self.wait_for(lambda r: r["state"] == "STOPPED")
        self.send(6, "arm", deadman=True)
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        self.process.send_signal(signal.SIGINT)
        self.wait_for(lambda r: r["reason"] == "program exit")
        self.assertEqual(self.process.wait(timeout=3), 0)

    def test_invalid_frame_stops_active_arm(self):
        self.send(1, "arm", deadman=True)
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        os.write(self.master, b'not-a-frame\n')
        record = self.wait_for(lambda r: r["state"] == "FAULT")
        self.assertIn("invalid serial input", record["reason"])

    def test_unterminated_frame_does_not_block_timeout(self):
        self.send(1, "arm", deadman=True)
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        os.write(self.master, b'{"v":1')
        self.assertEqual(self.wait_for(lambda r: r["state"] == "FAULT")["reason"],
                         "serial command timeout")

    def test_stop_discards_queued_arm(self):
        self.send(1, "arm", deadman=True)
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        os.write(self.master, b'{"v":1,"seq":2,"type":"stop"}\n'
                             b'{"v":1,"seq":3,"type":"arm","deadman":true}\n')
        self.wait_for(lambda r: r["state"] == "STOPPED")
        self.send(4, "target", deadman=True, joints=[0.1] * 6)
        self.assertEqual(self.wait_for(lambda r: True)["state"], "STOPPED")

    def test_disconnect_is_nonzero_exit(self):
        self.send(1, "arm", deadman=True)
        self.wait_for(lambda r: r["state"] == "ACTIVE")
        os.close(self.master)
        self.master = os.open("/dev/null", os.O_RDONLY)
        self.assertEqual(self.process.wait(timeout=3), 2)


if __name__ == "__main__":
    unittest.main()
