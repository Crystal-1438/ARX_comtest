#!/usr/bin/env python3
"""Single-arm ARX X5 monitor / serial teleoperation without ROS or network servers."""

import argparse
import importlib.util
import json
import math
from pathlib import Path
import signal
import socket
import sys
import time

from backends import MockArm, VendorArm, extension_path, load_sdk
from control import Controller, Limits
from protocol import JsonLineDecoder, ProtocolError

DEFAULT_SDK = Path(__file__).resolve().parent / "vendor/ARX_X5/py/arx_x5_python"


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


def emit(controller, joints, backend):
    print(json.dumps({
        "state": controller.state, "reason": controller.reason,
        "backend": backend, "stop_mode": controller.arm.stop_mode,
        "joints_rad": list(joints),
        "joints_deg": [round(math.degrees(q), 4) for q in joints],
        "host_read_monotonic": time.monotonic(),
    }, ensure_ascii=False), flush=True)


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
    limits = load_limits(args.limits, hardware and args.mode == "teleop")
    if 1 / args.rate >= limits.timeout:
        raise ValueError("control period must be shorter than command timeout")
    decoder = decoder_from_path(args.decoder)
    source = arm = controller = None
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
                    controller.stop(f"invalid serial input: {exc}", fault=True)
            joints = controller.tick(time.monotonic())
            if now >= next_print or controller.state != previous_state:
                emit(controller, joints, args.backend)
                next_print = now + 1 / args.print_rate
                previous_state = controller.state
            next_tick += 1 / args.rate
            delay = next_tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.monotonic()  # No burst of catch-up motion commands.
        controller.stop("program exit")
        emit(controller, controller.arm.read_joints(), args.backend)
        return 0
    finally:
        try:
            if arm is not None:
                arm.close()
        finally:
            if source is not None:
                source.close()
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
