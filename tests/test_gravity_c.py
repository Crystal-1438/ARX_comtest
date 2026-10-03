"""Host validation of the freestanding STM32 float implementation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(shutil.which("cc") and shutil.which("nm"), "C compiler and nm required")
class GravityCTests(unittest.TestCase):
    def test_float_c_physics_range_errors_and_no_runtime_dependencies(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="arx-gravity-c-test-") as directory:
            report = Path(directory) / "report.json"
            result = subprocess.run(
                [sys.executable, str(root / "gravity_compensation/c/verify.py"),
                 "--build-dir", directory, "--samples", "30", "--report", str(report)],
                check=True, text=True, capture_output=True, timeout=60)
            data = json.loads(report.read_text())
            self.assertLess(data["max_absolute_error_nm"], 1e-5, result.stdout)
            self.assertEqual(data["core_undefined_symbols"], [])
            self.assertGreater(data["configurations_including_output_modes"], 10000)
