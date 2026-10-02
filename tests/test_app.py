import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app import BUNDLED_SDK, check_decoder_for_hardware, decoder_from_path, load_limits, run
from backends import MockArm
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
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run(arguments(backend="sdk", model="2023", decoder=str(PROJECT / "leader_decoder.py"),
                              limits=limits_file(directory), operator_keys=True))

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
