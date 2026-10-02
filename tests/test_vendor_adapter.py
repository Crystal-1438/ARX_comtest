import unittest
from unittest.mock import Mock

from backends import VendorArm


class VendorAdapterTests(unittest.TestCase):
    def setUp(self):
        self.arm = VendorArm.__new__(VendorArm)
        self.arm.interface = Mock()
        self.arm.interface.get_joint_positions.return_value = [0.1] * 6 + [1.2]
        self.arm.active = False

    def test_capture_gripper_and_target_before_position_mode(self):
        self.arm.start((0.1,) * 6)
        calls = self.arm.interface.method_calls
        self.assertEqual([c[0] for c in calls], ["get_joint_positions", "set_catch",
                                                "set_joint_positions", "set_arm_status"])
        self.assertEqual(calls[1].args, (1.2,))
        self.assertEqual(calls[-1].args, (5,))

    def test_soft_stop_and_six_arm_joints(self):
        self.arm.stop()
        self.arm.interface.set_arm_status.assert_called_once_with(0)
        self.assertEqual(self.arm.read_joints(), (0.1,) * 6)
        with self.assertRaises(RuntimeError):
            self.arm.write_joints((0.2,) * 6)

    def test_read_gripper_is_the_seventh_channel_alone(self):
        self.assertEqual(self.arm.read_gripper(), 1.2)
        self.arm.interface.get_joint_positions.return_value = [0.1] * 6
        with self.assertRaises(RuntimeError):
            self.arm.read_gripper()
        self.arm.interface.get_joint_positions.return_value = [0.1] * 6 + [float("nan")]
        with self.assertRaises(RuntimeError):
            self.arm.read_gripper()

    def test_reading_the_gripper_never_sends_anything(self):
        self.arm.read_gripper()
        self.assertEqual(self.arm.interface.method_calls[0][0], "get_joint_positions")
        self.assertEqual(len(self.arm.interface.method_calls), 1)  # No set_catch.

    def test_write_gripper_is_set_catch_and_only_while_tracking(self):
        with self.assertRaises(RuntimeError):
            self.arm.write_gripper(0.5)
        self.arm.interface.set_catch.assert_not_called()
        self.arm.active = True
        self.arm.write_gripper(0.5)
        self.arm.interface.set_catch.assert_called_once_with(0.5)

    def test_nothing_but_a_finite_number_reaches_the_sdk(self):
        # No coercion: "0.5" and True are refused rather than converted, because
        # the command is produced by an interpolation and anything else is a bug
        # upstream of the motor.
        self.arm.active = True
        for value in (float("nan"), float("inf"), "0.5", True, None, [0.5]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.arm.write_gripper(value)
        self.arm.interface.set_catch.assert_not_called()

    def test_a_rejected_gripper_target_raises(self):
        self.arm.active = True
        self.arm.interface.set_catch.return_value = False
        with self.assertRaises(RuntimeError):
            self.arm.write_gripper(0.5)

    def test_the_stop_path_never_touches_the_gripper(self):
        # STOP, close and SOFT are the paths a fault takes. None of them may
        # move the jaws -- nothing here knows whether SOFT holds or releases
        # them, so the only safe thing is not to send anything.
        self.arm.active = True
        self.arm.stop()
        self.arm.close()
        self.arm.enable_gravity_compensation()
        self.arm.interface.set_catch.assert_not_called()

    def test_failed_target_does_not_enter_position_mode(self):
        self.arm.interface.set_joint_positions.return_value = False
        with self.assertRaises(RuntimeError):
            self.arm.start((0.1,) * 6)
        self.arm.interface.set_arm_status.assert_not_called()

    def test_missing_gripper_feedback_does_not_enable(self):
        self.arm.interface.get_joint_positions.return_value = [0.1] * 6
        with self.assertRaises(RuntimeError):
            self.arm.start((0.1,) * 6)
        self.arm.interface.set_arm_status.assert_not_called()

    def test_gravity_compensation_is_state_three_and_close_undoes_it(self):
        self.arm.enable_gravity_compensation()
        self.arm.close()
        self.assertEqual([c[0] for c in self.arm.interface.method_calls],
                         ["set_arm_status", "set_arm_status"])
        self.assertEqual(self.arm.interface.set_arm_status.call_args_list[0].args, (3,))
        # Nothing may leave the arm driven: the last word is always SOFT.
        self.assertEqual(self.arm.interface.set_arm_status.call_args_list[-1].args, (0,))

    def test_gravity_compensation_refused_while_a_target_is_tracked(self):
        self.arm.active = True
        with self.assertRaises(RuntimeError):
            self.arm.enable_gravity_compensation()
        self.arm.interface.set_arm_status.assert_not_called()

    def test_rejected_gravity_compensation_raises(self):
        self.arm.interface.set_arm_status.return_value = False
        with self.assertRaises(RuntimeError):
            self.arm.enable_gravity_compensation()


if __name__ == "__main__":
    unittest.main()
