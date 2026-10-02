import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app import (BUNDLED_SDK, check_decoder_for_hardware, decoder_from_path,
                 due_for_print, install_arm_check, load_limits, run)
from backends import MockArm
from control import Controller, Limits
from protocol import Command, JsonLineDecoder, ProtocolError

PROJECT = Path(__file__).resolve().parents[1]
LIMITS = {"lower": [-3.14, 0.0, 0.0, -1.57, -1.57, -2.09],
          "upper": [3.14, 3.65, 3.14, 1.57, 1.57, 2.09]}


def arguments(**overrides):
    values = dict(mode="teleop", backend="mock", model=None, demo=False, serial="unused",
                  limits=None, rate=100, decoder=None, leader_map=None, operator_keys=False,
                  baud=115200, stop_mode="soft", duration=0.05, print_rate=10, sdk_root=None,
                  can_port="can0")
    values.update(overrides)
    return argparse.Namespace(**values)


def limits_file(directory):
    path = Path(directory) / "limits.json"
    path.write_text(json.dumps(LIMITS), encoding="utf-8")
    return path


class AppTests(unittest.TestCase):
    def test_default_sdk_is_bundled_with_required_files(self):
        project = Path(__file__).resolve().parents[1]
        self.assertEqual(BUNDLED_SDK, project / "vendor/ARX_X5/py/arx_x5_python")
        for name in ("bimanual/src/single_arm_interface.cpp", "bimanual/script/x5.urdf",
                     "bimanual/script/x5_2025.urdf", "bimanual/lib/arx_x5_src/libarx_x5_src.so"):
            self.assertTrue((BUNDLED_SDK / name).is_file(), name)

    def test_custom_decoder_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "decoder.py"
            plugin.write_text(
                'from protocol import Command\n'
                'class Decoder:\n'
                '    def feed(self, data):\n'
                '        return [Command("stop", 1)] if data == b"STOP" else []\n'
                'def create_decoder():\n'
                '    return Decoder()\n'
            )
            self.assertEqual(decoder_from_path(plugin).feed(b"STOP"), [Command("stop", 1)])

    def test_hardware_requires_explicit_joint_limits(self):
        with self.assertRaises(ValueError):
            load_limits(None, hardware=True)

    def test_serial_error_closes_arm_and_port(self):
        arm = MockArm("soft")
        source = Mock()
        source.read.side_effect = OSError("device disconnected")
        with patch("app.MockArm", return_value=arm), patch("app.SerialInput", return_value=source), \
                patch.object(arm, "close", wraps=arm.close) as close:
            with self.assertRaises(OSError):
                run(arguments())
            close.assert_called_once()
        self.assertFalse(arm.active)
        source.close.assert_called_once()

    def test_protocol_error_resets_the_decoder_and_keeps_running(self):
        decoder = Mock(last_telemetry=None)
        decoder.feed.side_effect = ProtocolError("bad frame")
        source = Mock()
        source.read.return_value = b""
        with patch("app.decoder_from_path", return_value=decoder), \
                patch("app.SerialInput", return_value=source), \
                patch("app.MockArm", return_value=MockArm("soft")):
            self.assertEqual(run(arguments()), 0)
        # Without this a half-written frame gets spliced onto the next batch.
        decoder.reset.assert_called()

    def test_leader_map_flag_reaches_the_decoder(self):
        with tempfile.TemporaryDirectory() as directory:
            mapping = Path(directory) / "calibrated.json"
            mapping.write_text(json.dumps({"calibrated": True, "joints": [{}] * 6}),
                               encoding="utf-8")
            source = Mock()
            source.read.return_value = b""
            with patch.dict(os.environ), \
                    patch("app.SerialInput", return_value=source), \
                    patch("app.MockArm", return_value=MockArm("soft")):
                self.assertEqual(run(arguments(decoder=str(PROJECT / "leader_decoder.py"),
                                               leader_map=mapping)), 0)
                # run() exports the override; the decoder reads it at load time.
                self.assertEqual(os.environ["ARX_LEADER_MAP"], str(mapping))


class PrintThrottleTests(unittest.TestCase):
    """Status lines are on a timer, except when the answer is worth having now.

    A refusal keeps the state where it was, so keying only on the state would
    hide the reply to ``a`` behind the print interval -- at a rate low enough
    to actually read, seconds of it.
    """

    STOPPED = ("STOPPED", "startup")
    REFUSED = "refusing to arm: the leader and the arm are not in the same pose"

    def test_nothing_prints_before_the_interval(self):
        self.assertFalse(due_for_print(1.0, 2.0, self.STOPPED, *self.STOPPED))

    def test_the_interval_prints_again(self):
        self.assertTrue(due_for_print(2.0, 2.0, self.STOPPED, *self.STOPPED))

    def test_a_new_state_prints_at_once(self):
        self.assertTrue(due_for_print(1.0, 2.0, self.STOPPED, "ACTIVE",
                                      "armed at measured position"))

    def test_a_new_reason_prints_at_once_even_in_the_same_state(self):
        self.assertTrue(due_for_print(1.0, 2.0, self.STOPPED, "STOPPED", self.REFUSED))

    def test_the_reason_only_counts_while_it_is_the_last_thing_printed(self):
        seen = ("STOPPED", self.REFUSED)
        self.assertFalse(due_for_print(1.0, 2.0, seen, "STOPPED", self.REFUSED))


class ArmCheckWiringTests(unittest.TestCase):
    """Handing a decoder's ``anchor`` to the controller, which is the whole of
    the leader decoder's gate. If this line is dropped the decoder still
    computes verdicts and nothing ever asks it for one."""

    def control(self, decoder):
        controller = Controller(MockArm(), Limits((-3.0,) * 6, (3.0,) * 6), 0)
        install_arm_check(controller, decoder)
        return controller

    def test_a_decoder_that_offers_an_anchor_gets_it_installed(self):
        decoder = Mock(anchor=Mock(return_value=None))
        controller = self.control(decoder)
        self.assertIs(controller.pre_arm, decoder.anchor)
        controller.operator_arm(0)
        self.assertEqual(controller.state, "ACTIVE")
        self.assertEqual(len(decoder.anchor.call_args[0][0]), 6)

    def test_its_verdict_reaches_the_state_machine(self):
        decoder = Mock(anchor=Mock(return_value="the leader is somewhere else"))
        controller = self.control(decoder)
        controller.operator_arm(0)
        self.assertEqual(controller.state, "STOPPED")
        self.assertEqual(controller.reason,
                         "refusing to arm: the leader is somewhere else")
        self.assertFalse(controller.arm.active)

    def test_a_decoder_with_no_anchor_leaves_arming_alone(self):
        # JsonLineDecoder is the existing wire protocol; nothing about it moves.
        controller = self.control(JsonLineDecoder())
        self.assertIsNone(controller.pre_arm)
        controller.operator_arm(0)
        self.assertEqual(controller.state, "ACTIVE")


class HardwareGateTests(unittest.TestCase):
    """The leader mapping is uncalibrated, so hardware teleop must refuse it."""

    def write(self, directory, calibrated, **joint):
        path = Path(directory) / "leader_map.json"
        path.write_text(json.dumps({"calibrated": calibrated,
                                    "joints": [dict(joint) for _ in range(6)]}), encoding="utf-8")
        return path

    def leader(self, directory, calibrated):
        mapping = self.write(directory, calibrated)
        with patch.dict(os.environ, {"ARX_LEADER_MAP": str(mapping)}):
            return decoder_from_path(PROJECT / "leader_decoder.py")

    def test_a_decoder_that_says_nothing_about_itself_is_not_gated(self):
        # JsonLineDecoder is the existing wire protocol; it must be unaffected.
        check_decoder_for_hardware(JsonLineDecoder(), operator_keys=False)

    def test_uncalibrated_leader_mapping_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            decoder = self.leader(directory, calibrated=False)
            with self.assertRaises(ValueError) as caught:
                check_decoder_for_hardware(decoder, operator_keys=True)
        self.assertIn("not calibrated", str(caught.exception))

    def test_a_stream_only_decoder_needs_local_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            decoder = self.leader(directory, calibrated=True)
            with self.assertRaises(ValueError) as caught:
                check_decoder_for_hardware(decoder, operator_keys=False)
            self.assertIn("--operator-keys", str(caught.exception))
            check_decoder_for_hardware(decoder, operator_keys=True)

    def test_run_refuses_before_any_motor_is_constructed(self):
        # The map is named outright rather than left to the decoder's default:
        # that default is ./leader_map.json, so a real calibration sitting in the
        # working directory would let this through and reach for the serial port.
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ):
            with self.assertRaises(ValueError):
                run(arguments(backend="sdk", model="2023",
                              decoder=str(PROJECT / "leader_decoder.py"),
                              limits=limits_file(directory),
                              leader_map=self.write(directory, calibrated=False),
                              operator_keys=True))

    def test_mock_teleop_still_accepts_an_uncalibrated_decoder(self):
        # Watching a live stream is exactly what the uncalibrated mapping is for.
        source = Mock()
        source.read.return_value = b""
        with patch("app.SerialInput", return_value=source), \
                patch("app.MockArm", return_value=MockArm("soft")):
            self.assertEqual(run(arguments(decoder=str(PROJECT / "leader_decoder.py"))), 0)

    def test_operator_keys_are_rejected_outside_teleop(self):
        with self.assertRaises(ValueError):
            run(arguments(mode="monitor", operator_keys=True))


if __name__ == "__main__":
    unittest.main()
