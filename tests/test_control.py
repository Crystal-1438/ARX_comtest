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
            self.control.handle(Command("target", 2, (math.inf,) * 6, True), 0.1)

    def test_an_out_of_range_target_is_clamped_named_not_fatal(self):
        # The input going out of range must not end the session: stopping drops
        # the arm to zero torque and lets it fall, which is worse than holding
        # at the bound, and a hand pushing the leader a degree too far is not
        # distinguishable here from a target that is genuinely out of range. The
        # joint that had to be held is named so the operator can see why the arm
        # stopped following.
        self.arm_controller()
        self.control.handle(
            Command("target", 2, (0.0, 1.5, 0.0, 0.0, 0.0, 0.0), True), 0.01)
        self.assertEqual(self.control.state, "ACTIVE")
        self.assertEqual(self.control.target, (0.0, 1.0, 0.0, 0.0, 0.0, 0.0))
        self.assertEqual(self.control.saturated, [1])
        # Only the command is clamped, never the mapping: pulling the leader
        # back inside resumes exactly where it left off.
        self.control.handle(
            Command("target", 3, (0.0, 0.5, 0.0, 0.0, 0.0, 0.0), True), 0.02)
        self.assertEqual(self.control.target, (0.0, 0.5, 0.0, 0.0, 0.0, 0.0))
        self.assertEqual(self.control.saturated, [])

    def test_the_arm_lagging_past_a_bound_is_not_a_fault_of_its_own(self):
        # A clamped command parks on the bound, and an arm servoing onto it sits
        # a little past -- here J6, 0.05 past a 1.0 bound and well inside the
        # 0.15 following error. That lag is the tracker's business; an absolute
        # test against the envelope faults on the arm obeying the clamped
        # command, which is the outcome the clamp exists to avoid.
        self.arm.positions = (1.0,) * 6
        self.arm_controller()
        self.control.handle(Command("target", 2, (1.0,) * 5 + (2.0,), True), 0.01)
        self.assertEqual(self.control.saturated, [5])
        self.arm.positions = (1.0,) * 5 + (1.05,)
        self.control.tick(0.02)
        self.assertEqual(self.control.state, "ACTIVE")
        # The command stays on the bound rather than chasing the arm out.
        self.assertEqual(self.arm.positions, (1.0,) * 6)

    def test_stopping_clears_the_saturated_joints(self):
        # Nothing is being held at a bound once there is no command, and the
        # readout prints this list as the state it is in.
        self.arm_controller()
        self.control.handle(Command("target", 2, (2.0,) * 6, True), 0.01)
        self.assertEqual(self.control.saturated, list(range(6)))
        self.control.handle(Command("stop", 3), 0.02)
        self.assertEqual(self.control.saturated, [])

    def test_arming_an_arm_already_outside_the_envelope_is_refused_not_fatal(self):
        # The arm resting a fraction past its configured range is a real case:
        # the example envelope is not measured, and one arm sits on it. It has to
        # come back as a reason -- this is the operator's key path, where an
        # exception ends the run instead of answering the key.
        self.arm.positions = (0.0, 0.0, 0.0, 0.0, 0.0, 2.0)
        self.control.operator_arm(0)
        self.assertEqual(self.control.state, "STOPPED")
        self.assertIn("refusing to arm", self.control.reason)
        self.assertIn("J6 +2.000 not in [-1.000, +1.000]", self.control.reason)
        self.assertFalse(self.arm.active)

    def test_an_arm_far_from_the_command_faults_and_does_not_raise(self):
        # The envelope is no longer compared against feedback -- the command is
        # the thing that is kept inside it -- but an arm this far from what it
        # was told to do is caught by the tracker, which is the check that
        # actually bounds how far outside the arm can end up.
        #
        # A fault and not an exception: this runs outside the loop's decoder
        # guard, so raising would leave the state machine by way of main() and
        # take the process with it -- the arm would stop with an ERROR line
        # instead of a state the operator can read and clear.
        self.arm_controller()
        self.arm.positions = (0.0, 0.0, 0.0, 0.0, 0.0, 2.0)
        self.control.tick(0.01)
        self.assertEqual(self.control.state, "FAULT")
        self.assertEqual(self.control.reason, "joint following error")
        self.assertFalse(self.arm.active)

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


class PreArmTests(unittest.TestCase):
    """The veto on enabling the arm, and the one thing it has to be is
    unavoidable: ARM arrives from the wire as well as from the operator's key,
    and a check installed on only one of them is a check that can be stepped
    around. It also has to see the position the arm is started from -- a verdict
    on a different reading than the one the arm is enabled at would be about
    nothing."""

    def setUp(self):
        self.arm = MockArm()
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6), 0)
        self.seen = []

    def blocker(self, reason=None):
        def check(measured):
            self.seen.append(measured)
            return reason
        self.control.pre_arm = check

    def test_no_hook_leaves_arming_alone(self):
        # Every decoder that says nothing about itself, which is all of them but
        # the leader's, has to behave exactly as it did.
        self.assertIsNone(self.control.pre_arm)
        self.control.handle(Command("arm", 1, deadman=True), 0)
        self.assertEqual(self.control.state, "ACTIVE")

    def test_the_wire_path_is_checked_too(self):
        self.blocker("not in the same pose")
        self.control.handle(Command("arm", 1, deadman=True), 0)
        self.assertEqual(self.control.state, "STOPPED")
        self.assertEqual(self.control.reason, "refusing to arm: not in the same pose")
        self.assertFalse(self.arm.active)

    def test_the_operator_path_is_checked_too(self):
        self.blocker("not in the same pose")
        self.control.operator_arm(0)
        self.assertEqual(self.control.state, "STOPPED")
        self.assertIn("refusing to arm", self.control.reason)

    def test_a_refusal_never_touches_the_arm(self):
        self.blocker("not in the same pose")
        self.control.operator_arm(0)
        self.assertEqual(self.arm.writes, [])
        self.assertFalse(self.arm.active)

    def test_it_sees_the_position_the_arm_would_be_started_from(self):
        self.arm.positions = (0.3,) * 6
        self.blocker()
        self.control.operator_arm(0)
        self.assertEqual(self.seen, [(0.3,) * 6])
        self.assertEqual(self.control.state, "ACTIVE")
        self.assertEqual(self.arm.positions, (0.3,) * 6)

    def test_it_can_be_retried_after_a_refusal(self):
        # Nothing is latched: the operator moves the leader and presses again.
        self.blocker("not in the same pose")
        self.control.operator_arm(0)
        self.blocker()
        self.control.operator_arm(1)
        self.assertEqual(self.control.state, "ACTIVE")

    def test_a_fault_does_not_reach_the_hook(self):
        # ARM after a fault is already refused by the state machine, and the
        # hook must not be a way to clear one.
        self.control.stop("latched", fault=True)
        self.blocker()
        self.control.operator_arm(0)
        self.assertEqual(self.seen, [])
        self.assertEqual(self.control.state, "FAULT")

    def test_a_repeated_arm_does_not_re_check(self):
        self.blocker()
        self.control.operator_arm(0)
        self.control.operator_arm(1)
        self.assertEqual(len(self.seen), 1)


class OperatorChannelTests(unittest.TestCase):
    """The leader wire format carries no arm/stop, so local keys are the only
    way to enable the arm or to clear a latched fault."""

    def setUp(self):
        self.arm = MockArm()
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6), 0)

    def test_local_arm_captures_the_measured_pose(self):
        self.arm.positions = (0.3,) * 6
        self.control.operator_arm(0.1)
        self.assertEqual((self.control.state, self.control.target), ("ACTIVE", (0.3,) * 6))
        self.assertTrue(self.arm.active)

    def test_local_commands_are_exempt_from_the_wire_sequence(self):
        self.control.operator_arm(0.1)
        self.control.operator_stop()
        self.control.operator_arm(0.2)
        self.assertEqual(self.control.state, "ACTIVE")
        # An operator action must not consume or renumber wire sequences.
        self.assertEqual(self.control.last_seq, -1)
        self.control.handle(Command("target", 0, (0.5,) * 6, True), 0.3)
        self.assertEqual(self.control.last_seq, 0)

    def test_local_stop_clears_a_latched_fault(self):
        self.control.operator_arm(0.1)
        self.control.watchdog(1.0)
        self.assertEqual(self.control.state, "FAULT")
        self.control.operator_arm(1.1)
        self.assertEqual(self.control.state, "FAULT")  # still needs an explicit stop
        self.control.operator_stop()
        self.assertEqual(self.control.state, "STOPPED")
        self.control.operator_arm(1.2)
        self.assertEqual(self.control.state, "ACTIVE")

    def test_local_arm_does_nothing_when_already_active(self):
        self.control.operator_arm(0.1)
        self.arm.positions = (0.5,) * 6
        self.control.operator_arm(0.2)
        # Re-anchoring mid-motion would silently discard the slew limit.
        self.assertEqual(self.control.target, (0.0,) * 6)

    def test_local_stop_reports_why(self):
        self.control.operator_stop("panel button")
        self.assertEqual((self.control.state, self.control.reason), ("STOPPED", "panel button"))


if __name__ == "__main__":
    unittest.main()
