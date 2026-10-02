import math
import unittest
from unittest.mock import Mock

from backends import MockArm, VendorArm, UnsupportedStopMode
from control import Controller, GripperScale, Limits
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

    def test_the_gripper_input_rides_along_with_a_target(self):
        frame = JsonLineDecoder().feed(
            b'{"v":1,"seq":1,"type":"target","joints":[0,0,0,0,0,0],"gripper":0.25}\n')[0]
        self.assertEqual(frame.gripper_input, 0.25)
        self.assertEqual(frame.joints, (0.0,) * 6)

    def test_the_gripper_field_defaults_to_no_channel_at_all(self):
        # Positional callers predate this field, and a sender with no gripper
        # channel must keep meaning exactly what it meant before.
        self.assertIsNone(Command("stop", 1).gripper_input)
        self.assertEqual(Command("target", 1, (0.0,) * 6, True),
                         Command("target", 1, (0.0,) * 6, True, None))

    def test_the_gripper_input_must_be_a_fraction_of_travel(self):
        # NaN is the one that has to be named: it is a float, so only the
        # finiteness test catches it, and every comparison against it is False.
        for value in (b'-0.1', b'1.1', b'"0.5"', b'true', b'[0.5]', b'NaN', b'Infinity'):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                JsonLineDecoder().feed(
                    b'{"v":1,"seq":1,"type":"target","joints":[0,0,0,0,0,0],'
                    b'"gripper":' + value + b'}\n')

    def test_only_a_target_may_carry_a_gripper_input(self):
        for kind in (b'"arm"', b'"stop"'):
            with self.subTest(kind=kind), self.assertRaises(ProtocolError):
                JsonLineDecoder().feed(b'{"v":1,"seq":1,"type":' + kind + b',"gripper":0.5}\n')


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

    def test_the_command_is_a_trajectory_and_the_deadman_stops_it(self):
        # A step in the target is not passed straight through: the command is
        # the trajectory the joint's acceleration bound allows (td.py), so the
        # first tick moves by a few thousandths of a radian and the second by
        # more than the first -- it is still speeding up, which is the whole
        # point of not having a constant-rate ramp.
        self.arm_controller()
        self.control.handle(Command("target", 2, (0.5,) * 6, True), 0.01)
        self.control.tick(0.01)
        first = self.arm.positions[0]
        self.assertGreater(first, 0.0)
        self.assertLess(first, 0.01)
        self.control.tick(0.02)
        second = self.arm.positions[0] - first
        self.assertGreater(second, first)
        self.assertLess(self.arm.positions[0], 0.5)
        self.control.handle(Command("target", 3, (0.5,) * 6, False), 0.03)
        self.assertFalse(self.arm.active)

    def test_the_trajectory_never_passes_the_target(self):
        # The target is clamped into the envelope, so a trajectory that never
        # passes it is what keeps the command inside the envelope. One target
        # per tick, or the command timeout would end the run first.
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6, max_speed=2.0), 0)
        self.arm_controller()
        for step in range(1, 400):
            self.control.handle(Command("target", step + 1, (0.9,) * 6, True), 0.01 * step)
            self.control.tick(0.01 * step)
            for q in self.control.commanded:
                self.assertLessEqual(q, 0.9 + 1e-12)
        self.assertAlmostEqual(self.control.commanded[0], 0.9, places=9)

    def test_a_multi_turn_target_is_not_wrapped(self):
        # The leader's angle is unwrapped by the mapper and can sit past a whole
        # turn. Folded into 0..360 on the way to the differentiator, 370 would
        # look like 10 and the trajectory would swing most of a turn the wrong
        # way to reach it.
        self.control = Controller(self.arm, Limits((-10.0,) * 6, (10.0,) * 6, max_speed=2.0), 0)
        self.arm.positions = (math.radians(350.0),) * 6
        self.arm_controller()
        previous = self.arm.positions[0]
        for step in range(1, 200):
            self.control.handle(
                Command("target", step + 1, (math.radians(370.0),) * 6, True), 0.01 * step)
            self.control.tick(0.01 * step)
            self.assertGreaterEqual(self.control.commanded[0], previous - 1e-12)
            previous = self.control.commanded[0]
        self.assertLess(abs(self.control.commanded[0] - math.radians(370.0)), math.radians(0.01))

    def test_arming_starts_the_trajectory_where_the_arm_is(self):
        # Arming must not be a step: the trajectory starts at the measured pose
        # at rest, so the first tick commands that pose and nothing else.
        self.arm.positions = (0.3,) * 6
        self.arm_controller()
        self.control.handle(Command("target", 2, (0.3,) * 6, True), 0.01)
        self.control.tick(0.01)
        for actual in self.arm.positions:
            self.assertAlmostEqual(actual, 0.3, places=12)

    def test_the_acceleration_bound_is_the_configured_one(self):
        # Two loops, same step, different per-joint bound: the big one is the
        # one that has travelled further. This is the wire from limits.json.
        def after_one_tick(r_deg):
            arm = MockArm()
            control = Controller(arm, Limits((-1,) * 6, (1,) * 6, td_r_deg=(r_deg,) * 6), 0)
            control.handle(Command("arm", 1, deadman=True), 0)
            control.handle(Command("target", 2, (0.5,) * 6, True), 0.01)
            control.tick(0.01)
            return arm.positions[0]

        self.assertGreater(after_one_tick(4000.0), after_one_tick(400.0))

    def test_the_configured_rate_caps_the_trajectory(self):
        # The bound is on acceleration; ``max_speed`` is what bounds the rate.
        arm = MockArm()
        control = Controller(arm, Limits((-1,) * 6, (1,) * 6, max_speed=0.01,
                                         td_r_deg=(4000.0,) * 6), 0)
        control.handle(Command("arm", 1, deadman=True), 0)
        previous = 0.0
        for step in range(1, 50):
            control.handle(Command("target", step + 1, (1.0,) * 6, True), 0.01 * step)
            control.tick(0.01 * step)
            self.assertLessEqual(arm.positions[0] - previous, 0.01 * 0.01 + 1e-12)
            previous = arm.positions[0]

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

    def test_bad_acceleration_bounds_are_refused_at_construction(self):
        # A zero or negative bound would divide by zero in the differentiator
        # and a short tuple would silently leave joints on a default, so both
        # are configuration errors rather than something to clamp at run time.
        for bad in ((1.0,) * 5, (1.0,) * 7, (0.0,) * 6, (-1.0,) * 6,
                    (1.0,) * 5 + ("400",), float("nan")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Limits((-1,) * 6, (1,) * 6, td_r_deg=bad)


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
        # Re-anchoring mid-motion would silently restart the trajectory from a
        # pose the arm is not in.
        self.assertEqual(self.control.target, (0.0,) * 6)

    def test_local_stop_reports_why(self):
        self.control.operator_stop("panel button")
        self.assertEqual((self.control.state, self.control.reason), ("STOPPED", "panel button"))


class GripperScaleTests(unittest.TestCase):
    def test_the_two_stops_must_differ_and_be_finite(self):
        for pair in ((1.0, 1.0), (float("nan"), 0.0), (0.0, float("inf")),
                     (0.0, float("-inf")), ("0", 1.0), (True, False), (0.0, None)):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                GripperScale(*pair)

    def test_the_interpolation_clamps_and_does_not_assume_an_order(self):
        # Which end reads larger is a property of the gripper, not something to
        # validate: this one is closed at the smaller number.
        scale = GripperScale(open=2.0, closed=-1.5)
        self.assertEqual(scale.value(0.0), 2.0)
        self.assertEqual(scale.value(1.0), -1.5)
        self.assertEqual(scale.value(0.5), 0.25)
        self.assertEqual(scale.value(-3.0), 2.0)
        self.assertEqual(scale.value(7.0), -1.5)


class GripperFollowTests(unittest.TestCase):
    """The jaws follow the operator's input, and nothing else moves them."""

    def setUp(self):
        self.arm = MockArm()
        # Distinctive stops, neither of them 0 or 1: an interpolation that
        # forgot the span, or swapped the ends, cannot look right by accident.
        self.scale = GripperScale(open=-1.5, closed=2.0)
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6), 0,
                                  gripper=self.scale)
        self.seq = 0

    def send(self, kind, now, gripper=None, deadman=True):
        self.seq += 1
        joints = (0.0,) * 6 if kind == "target" else ()
        self.control.handle(Command(kind, self.seq, joints, deadman, gripper), now)

    def follow(self, value, now):
        self.send("target", now, gripper=value)
        self.control.tick(now)

    def test_zero_opens_and_one_closes(self):
        self.send("arm", 0.0)
        for value in (0.0, 0.5, 1.0, 0.25):
            with self.subTest(value=value):
                self.follow(value, 0.01 * (self.seq + 1))
                self.assertAlmostEqual(self.arm.gripper_writes[-1], self.scale.value(value))

    def test_a_target_while_stopped_is_remembered_not_sent(self):
        # The operator's choice: arming follows the input already in hand rather
        # than waiting for the next frame. Nothing moves before the arm is on.
        self.send("target", 0.01, gripper=0.75)
        self.assertEqual(self.arm.gripper_writes, [])
        self.assertEqual(self.control.gripper_input, 0.75)
        self.send("arm", 0.02)
        self.control.tick(0.03)
        self.assertEqual(self.arm.gripper_writes, [self.scale.value(0.75)])

    def test_the_deadman_release_stops_the_gripper_too(self):
        self.send("arm", 0.0)
        self.follow(1.0, 0.01)
        before = list(self.arm.gripper_writes)
        self.send("target", 0.02, gripper=0.0, deadman=False)
        self.control.tick(0.03)
        self.assertEqual(self.control.state, "STOPPED")
        self.assertEqual(self.arm.gripper_writes, before)
        self.assertIsNone(self.control.gripper_command)

    def test_a_timeout_fault_stops_the_gripper_too(self):
        self.send("arm", 0.0)
        self.follow(1.0, 0.01)
        before = list(self.arm.gripper_writes)
        self.control.tick(1.0)  # Past limits.timeout, with no command since.
        self.assertEqual(self.control.state, "FAULT")
        self.assertEqual(self.arm.gripper_writes, before)

    def test_re_arming_follows_the_input_held_now(self):
        self.send("arm", 0.0)
        self.follow(1.0, 0.01)
        self.control.operator_stop()
        self.send("target", 0.02, gripper=0.25)  # Arrives while stopped.
        self.assertEqual(len(self.arm.gripper_writes), 1)
        self.send("arm", 0.03)
        self.control.tick(0.04)
        # Not the 1.0 that was commanded before the stop: the input is what the
        # operator is holding, and it is the thing being followed.
        self.assertEqual(self.arm.gripper_writes[-1], self.scale.value(0.25))

    def test_an_unconfigured_gripper_is_never_written(self):
        self.control = Controller(self.arm, Limits((-1,) * 6, (1,) * 6), 0)
        self.send("arm", 0.0)
        self.follow(1.0, 0.01)
        self.assertEqual(self.arm.gripper_writes, [])

    def test_a_rejected_command_faults_instead_of_leaving_tick(self):
        self.send("arm", 0.0)
        self.arm.write_gripper = Mock(side_effect=RuntimeError("SDK rejected gripper target"))
        self.follow(1.0, 0.01)  # Must not raise: tick() is outside the loop's guard.
        self.assertEqual(self.control.state, "FAULT")
        self.assertIn("gripper command rejected", self.control.reason)
        self.assertIsNone(self.control.gripper_command)


class JammingGripperTests(unittest.TestCase):
    """A gripper that lags is not a tracking failure, whatever the jaws do."""

    def test_the_following_error_check_is_six_joints_wide(self):
        arm = MockArm()
        arm.write_gripper = lambda value: arm.gripper_writes.append(value)  # Never moves.
        control = Controller(arm, Limits((-1,) * 6, (1,) * 6), 0,
                             gripper=GripperScale(open=-1.5, closed=2.0))
        control.handle(Command("arm", 1, deadman=True), 0)
        for step in range(2, 40):
            control.handle(Command("target", step, (0.4,) * 6, True, 1.0), 0.01 * step)
            control.tick(0.01 * step)
        self.assertEqual(control.state, "ACTIVE")
        self.assertEqual(arm.gripper_writes[-1], 2.0)


if __name__ == "__main__":
    unittest.main()
