"""ARX vendor adapter, deliberately without speculative motor-disable commands."""

import importlib.util
from importlib.machinery import EXTENSION_SUFFIXES
import math
import os
from pathlib import Path
import socket
import sys

from protocol import vector6


class UnsupportedStopMode(RuntimeError):
    pass


class VendorChatter:
    """Keep the vendor SDK's console output out of the operator's display.

    The core library prints from C++ (it announces itself, and its destructor
    announces the motors it releases), so redirecting ``sys.stdout`` would not
    catch it: this moves the file descriptors instead. What it wrote is kept in a
    log rather than discarded, since it is the only trace of what its threads did.

    The caller writes its own output to the stream handed back, which is a
    duplicate of the real descriptor -- anything printed through fd 1 while this
    is open ends up in the log with the vendor's noise. It lives here rather than
    in either tool because both of them drive the vendor library and both need the
    operator's screen kept for their own status lines.
    """

    def __init__(self, path):
        self.path = path
        self.console_fd = None
        self.error_fd = None
        self.console = None
        self.log = None

    def __enter__(self):
        sys.stdout.flush()
        sys.stderr.flush()
        self.log = open(self.path, "ab")
        # Two separate duplicates: 1 and 2 are usually the same terminal, but
        # restoring 2 from the duplicate of 1 would lose a redirected stderr.
        self.console_fd = os.dup(1)
        self.error_fd = os.dup(2)
        self.console = open(self.console_fd, "w", buffering=1, encoding="utf-8")
        os.dup2(self.log.fileno(), 1)
        os.dup2(self.log.fileno(), 2)
        return self.console

    def __exit__(self, *exception):
        try:
            self.console.flush()
        finally:
            # Restore first, close second: the console object owns console_fd,
            # and 1 and 2 are our own duplicates by the time they go.
            os.dup2(self.console_fd, 1)
            os.dup2(self.error_fd, 2)
            self.console.close()
            os.close(self.error_fd)
            self.log.close()
        return False


def _gripper_value(value):
    """The one gripper command both arms accept: a finite number, or nothing.

    Strings are not coerced even though ``float()`` would take them: the value
    comes out of an interpolation, so anything else is a caller's bug, and a
    quiet conversion here would be the only place in this project that turns a
    wrong type into a motor command. ``bool`` is out for the same reason.
    """
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("gripper command must be a finite number")
    return float(value)


class MockArm:
    """Instantaneous simulation for I/O tests, not a dynamics or safety validation."""

    def __init__(self, stop_mode="disabled"):
        self.stop_mode = stop_mode
        self.positions = (0.0,) * 6
        self.gripper = 0.0
        self.active = False
        self.writes = []
        # Gripper commands are kept apart from joint writes on purpose: almost
        # every test in the suite reads ``writes`` to mean "the six joints the
        # loop sent", and mixing a scalar in would either break those or need
        # them all to learn to skip it.
        self.gripper_writes = []

    def stop(self):
        self.active = False

    def start(self, positions):
        self.positions = vector6(positions)
        self.active = True

    def read_joints(self):
        return self.positions

    def read_gripper(self):
        return self.gripper

    def write_joints(self, positions):
        if not self.active:
            raise RuntimeError("write while stopped")
        self.positions = vector6(positions)
        self.writes.append(self.positions)
        # Keep long-running mock sessions bounded.
        del self.writes[:-1000]

    def write_gripper(self, value):
        if not self.active:
            raise RuntimeError("gripper write while stopped")
        value = _gripper_value(value)
        self.gripper = value
        self.gripper_writes.append(value)
        del self.gripper_writes[:-1000]

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
    # Arm states the SDK accepts, read from the jump table ControllerBase::update()
    # indexes at .rodata:0x32040 in the pinned .so. Anything above 5 falls through
    # to PROTECT. Only SOFT, GRAVITY_COMPENSATION and POSITION_CONTROL are used here:
    #  0 SOFT                  zero torque; the arm sags and must be supported
    #  1 GO_HOME               moves the arm on its own -- never sent by this project
    #  2 PROTECT               protective stop; also the fallback for unknown values
    #  3 GRAVITY_COMPENSATION  motors hold the arm up; hand-guidable, still driven
    #  4 END_CONTROL           end-effector control, unused
    #  5 POSITION_CONTROL      tracks set_joint_positions()
    SOFT = 0
    GRAVITY_COMPENSATION = 3
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

    def enable_gravity_compensation(self):
        """Let the motors carry the arm's own weight so a hand can place it.

        This is state 3, the same thing the vendor's Python wrapper calls
        gravity_compensation(). It is NOT motor disable and NOT a stop mode: the
        joints are driven, back-drivable, and the arm holds its pose until it is
        pushed. The URDF dynamics decide the torques, so a payload the model does
        not know about makes it drift. Never entered while tracking a target --
        mode changes only from a stopped arm -- and stop()/close() undo it.
        """
        if self.active:
            raise RuntimeError("cannot change mode while tracking a target")
        self._check(self.interface.set_arm_status(self.GRAVITY_COMPENSATION),
                    "GRAVITY_COMPENSATION")

    def read_joints(self):
        values = list(self.interface.get_joint_positions())
        if len(values) not in (6, 7):
            raise RuntimeError("SDK returned unexpected joint count")
        # Seventh channel is the gripper, not joint7. This app controls six arm joints.
        return vector6(values[:6])

    def read_gripper(self):
        """The seventh channel on its own: the gripper, in whatever unit it uses.

        Read-only and used by exactly one caller, ``app.py --mode probe-gripper``,
        because that unit is not written down anywhere -- not in the header, not
        in the URDF, and not in the binary. ``start()`` already assumes the value
        it reads here is also what ``set_catch`` will accept; this measures the
        reading half of that assumption and cannot confirm the other half.
        """
        values = list(self.interface.get_joint_positions())
        if len(values) != 7:
            raise RuntimeError("SDK must report six joints plus gripper")
        if not math.isfinite(values[6]):
            raise RuntimeError("Invalid gripper feedback")
        return float(values[6])

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

    def write_gripper(self, value):
        """Command the gripper, in the same unit ``read_gripper`` reports.

        That the two units agree is an assumption, not a measurement -- it is
        what ``start()`` has always done, writing the feedback value straight
        back, and neither the header nor the URDF nor the binary says what
        ``set_catch`` expects. The two-stop probe observes the read side only.
        If the jaws go somewhere unexpected, or the SDK rejects the value, this
        is the first assumption to check.

        Only ever called while tracking a target: nothing on the stop path may
        reach it, so a SOFT stop cannot move the gripper.
        """
        if not self.active:
            raise RuntimeError("gripper write while stopped")
        self._check(self.interface.set_catch(_gripper_value(value)), "gripper target")

    def close(self):
        # Public SDK has no acknowledged disable/close. Stop and let process exit reap threads.
        self.stop()
