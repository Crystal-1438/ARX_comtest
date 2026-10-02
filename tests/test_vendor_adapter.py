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


if __name__ == "__main__":
    unittest.main()
