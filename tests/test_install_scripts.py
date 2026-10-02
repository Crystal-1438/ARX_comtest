import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def run_script(self, name, *args, **kwargs):
        return subprocess.run(["bash", str(PROJECT / "scripts" / name), *args],
                              text=True, capture_output=True, timeout=10, **kwargs)

    def test_sdk_dry_run_lists_dependencies_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            venv = Path(directory) / "environment with spaces"
            result = self.run_script("install_dependencies.sh", "--sdk", "--dry-run", "--venv", str(venv))
            self.assertEqual(result.returncode, 0, result.stderr)
            for text in ("libkdl-parser-dev", "liborocos-kdl-dev", "can-utils", "requirements-sdk.txt", "build_sdk.sh"):
                self.assertIn(text, result.stdout)
            self.assertFalse(venv.exists())

    def test_mock_skip_system_plan(self):
        result = self.run_script("install_dependencies.sh", "--mock", "--skip-system", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("requirements.txt", result.stdout)
        self.assertNotIn("apt-get", result.stdout)
        self.assertNotIn("build_sdk.sh", result.stdout)

    def test_missing_option_value_fails(self):
        result = self.run_script("install_dependencies.sh", "--venv")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Missing value", result.stderr)

    def test_missing_native_package_stops_before_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = {
                "sudo": '#!/bin/sh\nexec "$@"\n',
                "apt-get": '#!/bin/sh\nprintf "%s\\n" "$*" >> "$INSTALL_TEST_LOG"\n',
                "apt-cache": '#!/bin/sh\necho "  Candidate: (none)"\n',
            }
            for name, script in commands.items():
                path = root / name
                path.write_text(script)
                path.chmod(0o755)
            log = root / "apt.log"
            env = dict(os.environ, PATH=f'{root}:{os.environ["PATH"]}', INSTALL_TEST_LOG=str(log))
            result = self.run_script("install_dependencies.sh", "--sdk", env=env)
            self.assertEqual(result.returncode, 2)
            self.assertIn("No apt candidate", result.stderr)
            self.assertEqual(log.read_text().strip(), "update")

    def test_run_wrapper_relocates_and_selects_ready_sdk(self):
        with tempfile.TemporaryDirectory(prefix="arx relocated ") as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            for name in ("env.sh", "run.sh"):
                shutil.copy2(PROJECT / "scripts" / name, root / "scripts" / name)
            (root / ".venv/bin").mkdir(parents=True)
            (root / ".venv/bin/python").symlink_to(sys.executable)
            (root / "app.py").write_text('import os, sys, json\nprint(json.dumps([sys.argv[1:], os.environ["ARX_SDK_ROOT"]]))\n')
            env = dict(os.environ)
            env.pop("ARX_VENV_DIR", None)
            env.pop("ARX_SDK_ROOT", None)
            command = ["bash", str(root / "scripts/run.sh"), "--serial", "port with spaces"]
            def launch():
                result = subprocess.run(command, cwd="/tmp", env=env, capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            args, sdk = launch()
            self.assertEqual(args, ["--serial", "port with spaces"])
            self.assertEqual(sdk, str(root / "vendor/ARX_X5/py/arx_x5_python"))
            (root / ".sdk").mkdir()
            (root / ".sdk/READY").write_text("test")
            self.assertEqual(launch()[1], str(root / ".sdk"))

    def test_env_requires_source(self):
        result = self.run_script("env.sh")
        self.assertEqual(result.returncode, 2)
        self.assertIn("source scripts/env.sh", result.stderr)


if __name__ == "__main__":
    unittest.main()
