import argparse
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app import DEFAULT_SDK, decoder_from_path, load_limits, run
from backends import MockArm
from protocol import Command


class AppTests(unittest.TestCase):
    def test_default_sdk_is_bundled_with_required_files(self):
        project = Path(__file__).resolve().parents[1]
        self.assertEqual(DEFAULT_SDK, project / "vendor/ARX_X5/py/arx_x5_python")
        for name in ("bimanual/src/single_arm_interface.cpp", "bimanual/script/x5.urdf",
                     "bimanual/script/x5_2025.urdf", "bimanual/lib/arx_x5_src/libarx_x5_src.so"):
            self.assertTrue((DEFAULT_SDK / name).is_file(), name)

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
        args = argparse.Namespace(mode="teleop", backend="mock", model=None, demo=False,
                                  serial="unused", limits=None, rate=100, decoder=None,
                                  baud=115200, stop_mode="soft", duration=1, print_rate=10)
        arm = MockArm("soft")
        source = Mock()
        source.read.side_effect = OSError("device disconnected")
        with patch("app.MockArm", return_value=arm), patch("app.SerialInput", return_value=source), \
                patch.object(arm, "close", wraps=arm.close) as close:
            with self.assertRaises(OSError):
                run(args)
            close.assert_called_once()
        self.assertFalse(arm.active)
        source.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
