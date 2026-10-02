#!/usr/bin/env python3
"""Single-arm ARX X5 monitor / serial teleoperation without ROS or network servers."""

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import sys
import time

from backends import MockArm, VendorArm, extension_path, load_sdk
from control import Controller, Limits
from operator_keys import KeyInput, NullInput
from protocol import JsonLineDecoder, ProtocolError

BUNDLED_SDK = Path(__file__).resolve().parent / "vendor/ARX_X5/py/arx_x5_python"
DEFAULT_SDK = Path(os.environ.get("ARX_SDK_ROOT", str(BUNDLED_SDK)))


class SerialInput:
    def __init__(self, port, baudrate):
        import serial
        # Non-blocking reads keep the watchdog independent of incomplete frames.
        self.port = serial.Serial(port, baudrate, timeout=0, exclusive=True)
        self.port.reset_input_buffer()

    def read(self):
        if self.port.in_waiting > 4096:
            self.port.reset_input_buffer()
            raise ProtocolError("serial backlog exceeded 4096 bytes")
        return self.port.read(4096)

    def close(self):
        self.port.close()


class DemoInput:
    def __init__(self):
        self.started = time.monotonic()
        self.sequence = 0
        self.armed = False

    def read(self):
        elapsed = time.monotonic() - self.started
        if elapsed < 0.1:
            return b""
        self.sequence += 1
        frame = {"v": 1, "seq": self.sequence, "deadman": True}
        if elapsed >= 0.7:
            frame["type"] = "stop"
        elif not self.armed:
            frame["type"] = "arm"
            self.armed = True
        else:
            frame.update(type="target", joints=[0.05] * 6)
        return (json.dumps(frame) + "\n").encode()

    def close(self):
        pass


def decoder_from_path(path):
    if not path:
        return JsonLineDecoder()
    spec = importlib.util.spec_from_file_location("teleop_custom_decoder", Path(path).resolve())
    if spec is None or spec.loader is None:
        raise ValueError("decoder must be a Python file")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    decoder = module.create_decoder()
    if not callable(getattr(decoder, "feed", None)):
        raise ValueError("decoder must implement feed(bytes) -> list[Command]")
    return decoder


def load_limits(path, hardware=False):
    if not path:
        if hardware:
            raise ValueError("SDK teleop requires --limits with calibrated joint limits in radians")
        return Limits((-1.0,) * 6, (1.0,) * 6)
    with open(path, encoding="utf-8") as stream:
        config = json.load(stream)
    return Limits(**config)


def preflight(args):
    """No robot constructor, serial open, CAN activation, or motor commands."""
    report = {
        "python": sys.version.split()[0], "sdk_root": str(args.sdk_root),
        "interfaces": [name for _, name in socket.if_nameindex()],
        "stop_mode": args.stop_mode, "true_disable_supported": False,
        "errors": [],
    }
    if args.stop_mode != "soft":
        report["errors"].append("SDK has no public true motor-disable interface")
    try:
        report["extension"] = str(extension_path(args.sdk_root))
        module = load_sdk(args.sdk_root)
        for name in ("set_arm_status", "set_joint_positions", "get_joint_positions", "set_catch", "arx_x"):
            if not hasattr(module.InterfacesPy, name):
                report["errors"].append(f"SDK method missing: {name}")
        report["sdk_import"] = "ok (no arm constructed)"
    except (ImportError, OSError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    if args.can_port not in report["interfaces"]:
        report["errors"].append(f"CAN interface absent: {args.can_port}")
    else:
        directory = Path("/sys/class/net") / args.can_port
        if (directory / "type").read_text().strip() != "280":
            report["errors"].append(f"Not SocketCAN: {args.can_port}")
        if not int((directory / "flags").read_text().strip(), 16) & 1:
            report["errors"].append(f"Interface down: {args.can_port}")
    if args.serial and not Path(args.serial).exists():
        report["errors"].append(f"Serial device absent: {args.serial}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["errors"] else 0


def check_decoder_for_hardware(decoder, operator_keys):
    """Refuse to move real motors with a decoder that cannot do the job.

    Both checks are opt-in from the decoder side: a decoder that says nothing
    about itself (JsonLineDecoder) is left alone, so the existing wire protocol
    is unaffected.
    """
    if getattr(decoder, "calibrated", None) is False:
        raise ValueError(
            "decoder is not calibrated: fill in leader_map.json and set \"calibrated\": true "
            "(see leader_map.example.json) before driving hardware")
    if getattr(decoder, "provides_arm", True) is False and not operator_keys:
        raise ValueError(
            "decoder cannot send arm or stop, which the controller needs both to enable the "
            "arm and to clear a latched fault; add --operator-keys")


def apply_operator_arm(controller, decoder, now):
    """Arm on the operator's key, unless the decoder says this session is bad.

    The leader decoder fixes its unwrap origin on the first frame, so a session
    that started away from the calibrated pose is off by that much on every
    joint and cannot be corrected from here. Refusing leaves the reason on the
    readout instead of walking the arm. Only the operator path needs this: a
    decoder that can send ARM itself has to declare it, and this one declares it
    cannot (``provides_arm``), which is what --operator-keys is for.
    """
    blocker = getattr(decoder, "startup_blocker", None)
    if blocker and controller.state == "STOPPED":
        controller.stop(f"refusing to arm: {blocker}")
    else:
        controller.operator_arm(now)


def emit(controller, joints, backend, decoder=None):
    record = {
        "state": controller.state, "reason": controller.reason,
        "backend": backend, "stop_mode": controller.arm.stop_mode,
        "joints_rad": list(joints),
        "joints_deg": [round(math.degrees(q), 4) for q in joints],
        "host_read_monotonic": time.monotonic(),
    }
    # What the decoder last made of its input. joints_deg above is arm feedback,
    # so while nothing is armed this is the only way to watch a live stream.
    telemetry = getattr(decoder, "last_telemetry", None)
    if telemetry is not None:
        record["leader"] = telemetry
    print(json.dumps(record, ensure_ascii=False), flush=True)


def run(args):
    if args.mode == "preflight":
        return preflight(args)
    hardware = args.backend == "sdk"
    if hardware and not args.model:
        raise ValueError("--model 2023 or 2025 is required for hardware")
    if args.demo and (hardware or args.mode != "teleop"):
        raise ValueError("--demo is only for mock teleop")
    if args.mode == "teleop" and not (args.serial or args.demo):
        raise ValueError("teleop requires --serial (or --demo with mock)")
    if args.operator_keys and args.mode != "teleop":
        raise ValueError("--operator-keys only applies to teleop")
    limits = load_limits(args.limits, hardware and args.mode == "teleop")
    if 1 / args.rate >= limits.timeout:
        raise ValueError("control period must be shorter than command timeout")
    if args.leader_map:
        # Decoders are loaded through the argument-free create_decoder() contract,
        # so the override travels by environment rather than by parameter.
        os.environ["ARX_LEADER_MAP"] = str(args.leader_map)
    decoder = decoder_from_path(args.decoder)
    if hardware and args.mode == "teleop":
        check_decoder_for_hardware(decoder, args.operator_keys)
    source = arm = controller = operator = None
    interrupted = False
    previous_handlers = {}

    def request_stop(_signal, _frame):
        nonlocal interrupted
        interrupted = True

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, request_stop)
        # Open serial before connecting motors so serial-open failure cannot enable an arm.
        if args.mode == "teleop":
            source = DemoInput() if args.demo else SerialInput(args.serial, args.baud)
            operator = KeyInput() if args.operator_keys else NullInput()
        arm = (VendorArm(args.sdk_root, args.can_port, args.model, args.stop_mode)
               if hardware else MockArm(args.stop_mode))
        controller = Controller(arm, limits, time.monotonic())
        started = time.monotonic()
        next_tick = next_print = started
        previous_state = None
        while not interrupted:
            now = time.monotonic()
            if args.duration and now - started >= args.duration:
                break
            controller.watchdog(now)
            if operator:
                # Local keys go first: an operator STOP has to land before the
                # wire frames already sitting in this iteration's buffer.
                for action in operator.poll():
                    if action == "arm":
                        apply_operator_arm(controller, decoder, time.monotonic())
                    else:
                        controller.operator_stop()
            if source:
                try:
                    commands = decoder.feed(source.read())
                    if not isinstance(commands, list) or len(commands) > 64:
                        raise ProtocolError("decoder must return at most 64 commands per batch")
                    for command in commands:
                        controller.handle(command, time.monotonic())
                        if command.kind == "stop" or not command.deadman:
                            break  # Discard targets/ARM queued behind STOP in the same batch.
                except ProtocolError as exc:
                    # A decoder holding a half-written frame must drop it too, or
                    # the next bytes get spliced onto a fragment of the last one.
                    getattr(decoder, "reset", lambda: None)()
                    controller.stop(f"invalid serial input: {exc}", fault=True)
            joints = controller.tick(time.monotonic())
            if now >= next_print or controller.state != previous_state:
                emit(controller, joints, args.backend, decoder)
                next_print = now + 1 / args.print_rate
                previous_state = controller.state
            next_tick += 1 / args.rate
            delay = next_tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.monotonic()  # No burst of catch-up motion commands.
        controller.stop("program exit")
        emit(controller, controller.arm.read_joints(), args.backend, decoder)
        return 0
    finally:
        try:
            if arm is not None:
                arm.close()
        finally:
            if source is not None:
                source.close()
            if operator is not None:
                operator.close()  # Restores the terminal before the process exits.
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)


def positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("monitor", "teleop", "preflight"), default="monitor")
    parser.add_argument("--backend", choices=("mock", "sdk"), default="mock")
    parser.add_argument("--stop-mode", choices=("soft", "disabled"), default="soft",
                        help="SOFT is zero torque, not motor disable; SDK disabled mode is unsupported")
    parser.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--model", choices=("2023", "2025"))
    parser.add_argument("--can-port", default="can0")
    parser.add_argument("--serial", help="teleoperation controller port, NOT the USB2CAN serial port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--decoder", help="custom Python decoder file exposing create_decoder()")
    parser.add_argument("--leader-map", type=Path,
                        help="leader calibration JSON; overrides ARX_LEADER_MAP and leader_map.json")
    parser.add_argument("--operator-keys", action="store_true",
                        help="arm with 'a', stop with 's' on stdin; the leader wire has neither")
    parser.add_argument("--limits", type=Path, help="JSON limits in vendor joint coordinates/radians")
    parser.add_argument("--rate", type=positive, default=100.0)
    parser.add_argument("--print-rate", type=positive, default=10.0)
    parser.add_argument("--duration", type=positive, help="optional runtime in seconds")
    parser.add_argument("--demo", action="store_true", help="mock-only generated JSON input")
    args = parser.parse_args(argv)
    if args.baud <= 0:
        parser.error("baud must be positive")
    try:
        return run(args)
    except (OSError, RuntimeError, ValueError, ImportError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
