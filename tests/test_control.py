import math
import unittest

from backends import MockArm, VendorArm, UnsupportedStopMode
from control import Controller, Limits
from protocol import Command, JsonLineDecoder, ProtocolError


class ProtocolTests(unittest.TestCase):
    def test_fragmentation_and_multiple_frames(self):
        decoder = JsonLineDecoder()
        self.assertEqual(decoder.feed(b'{"v":1,"seq":'), [])
        frames = decoder.feed(b'1,"type":"stop"}\n{"v":1,"seq":2,"type":"arm","deadman":true}\n')
        self.assertEqual([f.kind for f in frames], ["stop", "arm"])

    def test_reject_malformed_and_ambiguous_frames(self):
        for data in (b'[]\n', b'{"v":true}\n', b'\xff\n',
                     b'{"v":1,"v":1,"seq":1,"type":"stop"}\n',
                     b'{"v":1,"seq":true,"type":"stop"}\n',
                     b'{"v":1,"seq":1,"type":"target","joints":[NaN,0,0,0,0,0]}\n',
                     b'{"v":1,"seq":1,"type":"target","joints":[0,0]}\n'):
            with self.subTest(data=data), self.assertRaises(ProtocolError):
                JsonLineDecoder().feed(data)

    def test_oversize_and_recovery(self):
        decoder = JsonLineDecoder(64)
        with self.assertRaises(ProtocolError):
            decoder.feed(b'x' * 65)
        self.assertEqual(decoder.feed(b'{"v":1,"seq":1,"type":"stop"}\n')[0].kind, "stop")


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.arm = MockArm()
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6), 0)

    def arm_controller(self):
        self.control.handle(Command("arm", 1, deadman=True), 0)

    def test_stopped_reads_without_writes(self):
        self.arm.positions = (0.3,) * 6
        self.assertEqual(self.control.tick(0.1), self.arm.positions)
        self.assertEqual(self.arm.writes, [])
        self.assertFalse(self.arm.active)

    def test_target_cannot_enable_and_arm_captures_measured_pose(self):
        self.control.handle(Command("target", 0, (0.5,) * 6, True), 0)
        self.assertFalse(self.arm.active)
        self.arm.positions = (0.3,) * 6
        self.arm_controller()
        self.assertEqual(self.control.target, (0.3,) * 6)

    def test_slew_limit_and_deadman(self):
        self.arm_controller()
        self.control.handle(Command("target", 2, (0.5,) * 6, True), 0.01)
        self.control.tick(0.01)
        self.assertAlmostEqual(self.arm.positions[0], 0.002)
        self.control.handle(Command("target", 3, (0.5,) * 6, False), 0.02)
        self.assertFalse(self.arm.active)

    def test_timeout_latches_until_stop_then_arm(self):
        self.arm_controller()
        self.control.watchdog(0.3)
        self.control.handle(Command("arm", 2, deadman=True), 0.3)
        self.control.handle(Command("target", 3, (0.5,) * 6, True), 0.3)
        self.assertEqual(self.control.state, "FAULT")
        self.control.handle(Command("stop", 4), 0.31)
        self.control.handle(Command("arm", 5, deadman=True), 0.32)
        self.assertEqual(self.control.state, "ACTIVE")

    def test_repeated_arm_does_not_refresh_watchdog(self):
        self.arm_controller()
        self.control.handle(Command("arm", 2, deadman=True), 0.2)
        self.control.tick(0.3)
        self.assertEqual(self.control.state, "FAULT")

    def test_sequence_and_limits(self):
        self.arm_controller()
        with self.assertRaises(ProtocolError):
            self.control.handle(Command("target", 1, (0,) * 6, True), 0.1)
        with self.assertRaises(ProtocolError):
            self.control.handle(Command("target", 2, (2,) * 6, True), 0.1)
        with self.assertRaises(ProtocolError):
            self.control.handle(Command("target", 3, (math.inf,) * 6, True), 0.1)

    def test_following_error_stops(self):
        self.arm_controller()
        self.arm.positions = (0.5,) * 6
        self.control.tick(0.01)
        self.assertEqual(self.control.state, "FAULT")
        self.assertFalse(self.arm.active)

    def test_stop_is_honored_despite_old_sequence(self):
        self.arm_controller()
        self.control.handle(Command("stop", 0), 0.1)
        self.assertFalse(self.arm.active)
        self.assertEqual(self.control.last_seq, 1)

    def test_hardware_disable_is_rejected_before_sdk_construction(self):
        with self.assertRaises(UnsupportedStopMode):
            VendorArm("/nonexistent", "can0", "2023", "disabled")


if __name__ == "__main__":
    unittest.main()
