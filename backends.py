"""ARX vendor adapter, deliberately without speculative motor-disable commands."""

import importlib.util
from importlib.machinery import EXTENSION_SUFFIXES
import math
from pathlib import Path
import socket

from protocol import vector6


class UnsupportedStopMode(RuntimeError):
    pass


class MockArm:
    """Instantaneous simulation for I/O tests, not a dynamics or safety validation."""

    def __init__(self, stop_mode="disabled"):
        self.stop_mode = stop_mode
        self.positions = (0.0,) * 6
        self.active = False
        self.writes = []

    def stop(self):
        self.active = False

    def start(self, positions):
        self.positions = vector6(positions)
        self.active = True

    def read_joints(self):
        return self.positions

    def write_joints(self, positions):
        if not self.active:
            raise RuntimeError("write while stopped")
        self.positions = vector6(positions)
        self.writes.append(self.positions)
        # Keep long-running mock sessions bounded.
        del self.writes[:-1000]

    def close(self):
        self.stop()


def extension_path(sdk_root):
    directory = Path(sdk_root) / "bimanual/api/arx_x5_python"
    for suffix in EXTENSION_SUFFIXES:
        candidate = directory / ("arx_x5_python" + suffix)
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        f"No extension compatible with this Python in {directory}; "
        "build the vendor extension for this interpreter and architecture."
    )


def load_sdk(sdk_root):
    # Import only the binding needed here, avoiding the unrelated solver dependency.
    path = extension_path(sdk_root)
    spec = importlib.util.spec_from_file_location("arx_x5_python", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VendorArm:
    SOFT = 0
    POSITION_CONTROL = 5

    def __init__(self, sdk_root, can_port, model, stop_mode):
        if stop_mode != "soft":
            raise UnsupportedStopMode(
                "This SDK does not expose motor disable + disabled feedback. "
                "No hardware connection was attempted. SOFT (0) is NOT motor disable."
            )
        if model not in ("2023", "2025"):
            raise ValueError("select the physical X5 model: 2023 or 2025")
        socket.if_nametoindex(can_port)
        if not int((Path("/sys/class/net") / can_port / "flags").read_text().strip(), 16) & 1:
            raise RuntimeError(f"CAN interface {can_port} is down")
        if (Path("/sys/class/net") / can_port / "type").read_text().strip() != "280":
            raise RuntimeError(f"{can_port} is not a SocketCAN interface")
        urdf = Path(sdk_root) / "bimanual/script" / (
            "x5.urdf" if model == "2023" else "x5_2025.urdf"
        )
        if not urdf.is_file():
            raise RuntimeError(f"Missing URDF: {urdf}")
        sdk = load_sdk(sdk_root)
        self.stop_mode = stop_mode
        self.active = False
        # Constructor itself starts vendor threads and may enable motors.
        self.interface = sdk.InterfacesPy(str(urdf.resolve()), can_port, 0 if model == "2023" else 2)
        try:
            self.stop()
            self.interface.arx_x(500, 2000, 10)  # Same tuning as vendor SingleArm.
        except BaseException:
            self.stop()
            raise

    @staticmethod
    def _check(result, operation):
        if result is False:
            raise RuntimeError(f"SDK rejected {operation}")

    def stop(self):
        self.active = False
        self._check(self.interface.set_arm_status(self.SOFT), "SOFT")

    def read_joints(self):
        values = list(self.interface.get_joint_positions())
        if len(values) not in (6, 7):
            raise RuntimeError("SDK returned unexpected joint count")
        # Seventh channel is the gripper, not joint7. This app controls six arm joints.
        return vector6(values[:6])

    def start(self, positions):
        # POSITION_CONTROL also runs the vendor gripper controller. Preserve its pose.
        feedback = list(self.interface.get_joint_positions())
        if len(feedback) != 7:
            raise RuntimeError("SDK must report six joints plus gripper before enabling control")
        if not math.isfinite(feedback[6]):
            raise RuntimeError("Invalid gripper feedback")
        self._check(self.interface.set_catch(feedback[6]), "initial gripper position")
        self._check(self.interface.set_joint_positions(list(vector6(positions))), "initial target")
        self._check(self.interface.set_arm_status(self.POSITION_CONTROL), "POSITION_CONTROL")
        self.active = True

    def write_joints(self, positions):
        if not self.active:
            raise RuntimeError("write while stopped")
        self._check(self.interface.set_joint_positions(list(vector6(positions))), "joint target")

    def close(self):
        # Public SDK has no acknowledged disable/close. Stop and let process exit reap threads.
        self.stop()
