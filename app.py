#!/usr/bin/env python3
"""Single-arm ARX X5 monitor / serial teleoperation without ROS or network servers."""

import argparse
from contextlib import ExitStack
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import sys
import time

from backends import MockArm, VendorArm, VendorChatter, extension_path, load_sdk
from control import Controller, GripperScale, Limits
from operator_keys import KeyInput, NullInput
from protocol import JsonLineDecoder, ProtocolError

BUNDLED_SDK = Path(__file__).resolve().parent / "vendor/ARX_X5/py/arx_x5_python"
DEFAULT_SDK = Path(os.environ.get("ARX_SDK_ROOT", str(BUNDLED_SDK)))
# Where the vendor SDK's own console output goes while the arm is open. It
# announces itself on construction and its destructor announces the motors it
# releases, and both would otherwise land in the middle of the readout.
DEFAULT_ARM_LOG = "teleop_arm.log"


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
    """The joint envelope, and the gripper calibration if the file carries one.

    Returns ``(Limits, GripperScale or None)``. The ``gripper`` key is lifted out
    before ``Limits`` is built: the two are different kinds of number -- one is
    the envelope that decides whether the arm may be enabled at all, the other a
    pair of measured stops -- and feeding one dict into one dataclass is exactly
    how the next reader ends up unable to tell them apart.

    No key means the gripper is not configured, and the whole write path is then
    unreachable. There is no default pair to fall back on: the stops can only be
    measured on the arm (``--mode probe-gripper``), so anything invented here
    would be a guess with a motor on the other end of it. A malformed pair raises
    on the spot, before any arm is constructed.
    """
    if not path:
        if hardware:
            raise ValueError("SDK teleop requires --limits with calibrated joint limits in radians")
        return Limits((-1.0,) * 6, (1.0,) * 6), None
    with open(path, encoding="utf-8") as stream:
        config = json.load(stream)
    gripper = None
    if isinstance(config, dict) and "gripper" in config:
        config = dict(config)
        # Strict on both the shape and the key names: a misspelled endpoint that
        # is quietly ignored would leave the scale built from a default that does
        # not exist, or worse, from a stale one.
        section = config.pop("gripper")
        if not isinstance(section, dict) or set(section) != {"open", "closed"}:
            raise ValueError('the "gripper" section needs exactly "open" and "closed"')
        try:
            gripper = GripperScale(section["open"], section["closed"])
        except ValueError as exc:
            raise ValueError(f"gripper: {exc}") from exc
    return Limits(**config), gripper


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


PROBE_OPEN = "Push the gripper jaws to FULLY OPEN by hand, hold them there, then press Enter."
PROBE_CLOSED = "Now push them to FULLY CLOSED by hand, hold, then press Enter."


def _await_enter(stream):
    """Block for one line on stdin; False when there is no stdin left to read."""
    try:
        # No argument: input() writes its prompt to sys.stdout, which is the
        # vendor's log file while VendorChatter is open. The prompt is printed
        # to `stream` instead.
        input()
    except EOFError:
        print("no stdin to read a prompt from", file=stream, flush=True)
        return False
    return True


def probe_endpoints(arm, stream):
    """Two labelled readings, so open and closed cannot be swapped by accident."""
    print(PROBE_OPEN, file=stream, flush=True)
    if not _await_enter(stream):
        return 2
    opened = arm.read_gripper()
    print(f"  held against the open stop:   {opened:+.6f}", file=stream, flush=True)
    print(PROBE_CLOSED, file=stream, flush=True)
    if not _await_enter(stream):
        return 2
    closed = arm.read_gripper()
    print(f"  held against the closed stop: {closed:+.6f}", file=stream, flush=True)
    if opened == closed:
        print("Both readings are identical, so the jaws did not move between the two "
              "prompts -- or channel 7 is not the gripper on this SDK. Nothing to "
              "write down.", file=stream, flush=True)
        return 2
    print("Add this to limits.json, then brace the arm before a real session:",
          file=stream, flush=True)
    print(json.dumps({"gripper": {"open": opened, "closed": closed}}, indent=2),
          file=stream, flush=True)
    print("The endpoints come from the reading above; set_catch is assumed to take "
          "the same unit, which this cannot confirm.", file=stream, flush=True)
    return 0


def probe_stream(arm, args, stream, stopping):
    """No terminal: print the channel with a running min and max until stopped."""
    lowest = highest = None
    started = time.monotonic()
    while not stopping():
        if args.duration and time.monotonic() - started >= args.duration:
            break
        value = arm.read_gripper()
        lowest = value if lowest is None else min(lowest, value)
        highest = value if highest is None else max(highest, value)
        print(f"gripper {value:+.6f}   min {lowest:+.6f}   max {highest:+.6f}",
              file=stream, flush=True)
        time.sleep(1 / args.print_rate)
    return 0


def probe_gripper(args):
    """Print the arm's gripper channel, and command nothing at all.

    The two endpoints the teleoperation mapping needs cannot be derived from the
    SDK: the header gives set_catch no unit, the URDF has no gripper joint, and
    the implementation stores the value unchecked. So they are measured here --
    by hand, with the arm held in SOFT (zero torque), which is where
    constructing the vendor interface leaves it.

    Nothing in this path writes: no Controller is built, no start(), no
    set_catch, no POSITION_CONTROL and no gravity compensation. That is also why
    it cannot confirm the one thing the mapping rests on -- that set_catch takes
    the unit channel 7 reports, which VendorArm.start() merely assumes.
    """
    hardware = args.backend == "sdk"
    if hardware and not args.model:
        raise ValueError("--model 2023 or 2025 is required for hardware")
    interactive = sys.stdin.isatty()
    interrupted = False
    previous_handlers = {}
    stream = sys.stdout
    stack = ExitStack()
    arm = None

    def request_stop(_signal, _frame):
        nonlocal interrupted
        interrupted = True

    try:
        if not interactive:
            for signum in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[signum] = signal.signal(signum, request_stop)
        if hardware:
            stream = stack.enter_context(VendorChatter(args.arm_log))
        arm = (VendorArm(args.sdk_root, args.can_port, args.model, args.stop_mode)
               if hardware else MockArm(args.stop_mode))
        print("The arm is in SOFT: zero torque, so it sags. Support it first. "
              "This mode reads one channel and commands nothing.", file=stream, flush=True)
        if interactive:
            return probe_endpoints(arm, stream)
        return probe_stream(arm, args, stream, lambda: interrupted)
    except KeyboardInterrupt:
        # Deliberately left to the default handler on the interactive path: a
        # Python signal handler would make the blocked input() restart, and Ctrl+C
        # at a prompt would appear to do nothing.
        print("interrupted; nothing was commanded", file=stream, flush=True)
        return 2
    finally:
        try:
            if arm is not None:
                arm.close()
        finally:
            stack.close()
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)


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


def install_arm_check(controller, decoder):
    """Let a decoder veto enabling the arm, and hand it the measured position.

    The leader decoder needs this: a single-turn encoder cannot say which turn
    it is on, so the whole-turn bias it carries has to be chosen against the
    pose the arm is actually in, and the moment just before the arm is enabled
    is the only time both readings are on hand. A decoder that says nothing
    about itself (``JsonLineDecoder``) has no such hook and is unaffected.

    This is a controller-level check rather than one on the operator's key
    because ARM reaches the controller by two routes -- the wire, and the local
    key -- and a decoder that emits ARM frames has to be held to the same check
    as an operator who presses the key.
    """
    controller.pre_arm = getattr(decoder, "anchor", None)


def due_for_print(now, next_print, seen, state, reason):
    """Whether this pass prints a status line.

    On a timer, but a change of state or reason prints at once whatever the
    timer says. A refusal leaves the state exactly where it was and only
    rewrites the reason, so on the timer alone the answer to pressing a would
    come out up to a whole print interval later -- and that is the one moment
    the operator is standing there waiting for it. Reading the two together
    also means the loop never has to print merely because it noticed a change.
    """
    return now >= next_print or (state, reason) != seen


def watch_line(clock, controller, joints, decoder):
    """One line for a person, instead of the JSON record.

    The JSON record carries everything and is unreadable at any rate a person
    can watch. This is the other half of the same data: the state, and -- while
    stopped -- how far each joint still has to be turned to be in the pose the
    arm is in, which is the number the operator is moving the leader to zero.
    The gate and this display are the same measurement, so the line turns good
    exactly when pressing a would work. While armed it is the other end of the
    same envelope: which joints the clamp is holding at their bound.

    A decoder need not offer it; one that does not gets the state alone, which
    is all a wire protocol with its own arm/stop can be watched for.
    """
    line = f"{clock} {controller.state:<7}"
    if controller.state != "STOPPED":
        # A clamped arm holds still while the leader keeps being pushed, and
        # without this the line would look exactly like an arm lagging behind.
        # Which joint is at its bound is the only thing that says whether the
        # session is following the hand or has run out of envelope.
        saturated = list(controller.saturated)
        held = ("  | at the limit: " + " ".join(f"J{index + 1}" for index in saturated)
                if saturated else "")
        return f"{line} | {controller.reason}{held}"
    distance = getattr(decoder, "distance", None)
    reading = distance(joints) if distance is not None else None
    if reading is None:
        return f"{line} | waiting for the leader's first frame"
    line += " | " + "  ".join(f"J{index + 1} {turn:+6.1f}"
                              for index, turn in enumerate(reading["turn_deg"]))
    if reading["outside"]:
        return line + "  | out of pose: " + " ".join(
            f"J{index + 1}" for index in reading["outside"]) + (
            f" (tolerance {reading['tolerance_deg']:.0f} deg)")
    return line + "  | in the arm's pose, press a"


def publish(controller, joints, backend, decoder, stream, watch):
    """Write this pass's line: the machine record, or the one a person reads."""
    if watch:
        print(watch_line(time.strftime("%H:%M:%S"), controller, joints, decoder),
              file=stream, flush=True)
    else:
        emit(controller, joints, backend, decoder, stream)


def emit(controller, joints, backend, decoder=None, stream=None):
    record = {
        "state": controller.state, "reason": controller.reason,
        "backend": backend, "stop_mode": controller.arm.stop_mode,
        "joints_rad": list(joints),
        "joints_deg": [round(math.degrees(q), 4) for q in joints],
        "host_read_monotonic": time.monotonic(),
    }
    # Present only once the gripper is configured, so an unconfigured setup
    # records exactly what it recorded before. "input" is the normalized leader
    # value and is null until a frame carrying one arrives, which is how a
    # configured-but-silent channel shows up; "command" is the arm value last
    # written, and stays null until the loop is ACTIVE. Neither is in the
    # decoder's own units -- the raw ADC stays under leader.frame.gripper.
    if controller.gripper is not None:
        record["gripper"] = {"input": controller.gripper_input,
                             "command": controller.gripper_command}
    # What the decoder last made of its input. joints_deg above is arm feedback,
    # so while nothing is armed this is the only way to watch a live stream.
    telemetry = getattr(decoder, "last_telemetry", None)
    if telemetry is not None:
        record["leader"] = telemetry
    print(json.dumps(record, ensure_ascii=False), file=stream or sys.stdout, flush=True)


def run(args):
    if args.mode == "preflight":
        return preflight(args)
    if args.mode == "probe-gripper":
        return probe_gripper(args)
    hardware = args.backend == "sdk"
    if hardware and not args.model:
        raise ValueError("--model 2023 or 2025 is required for hardware")
    if args.demo and (hardware or args.mode != "teleop"):
        raise ValueError("--demo is only for mock teleop")
    if args.mode == "teleop" and not (args.serial or args.demo):
        raise ValueError("teleop requires --serial (or --demo with mock)")
    if args.operator_keys and args.mode != "teleop":
        raise ValueError("--operator-keys only applies to teleop")
    limits, gripper = load_limits(args.limits, hardware and args.mode == "teleop")
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
    stream = sys.stdout
    stack = ExitStack()

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
        # Entered here, after the serial port is open so a failure to open it is
        # still reported on the real console, and left open until after arm.close()
        # below: the vendor library announces itself on construction and its
        # destructor announces the motors it releases, and the readout is where
        # neither belongs. Everything this program prints goes to `stream`, the
        # duplicate taken before the redirection.
        if hardware:
            stream = stack.enter_context(VendorChatter(args.arm_log))
        arm = (VendorArm(args.sdk_root, args.can_port, args.model, args.stop_mode)
               if hardware else MockArm(args.stop_mode))
        controller = Controller(arm, limits, time.monotonic(), gripper=gripper)
        install_arm_check(controller, decoder)
        started = time.monotonic()
        next_tick = next_print = started
        previous = None  # (state, reason) of the last printed line
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
                        # Goes through the same pre_arm check as the wire's ARM,
                        # installed above.
                        controller.operator_arm(time.monotonic())
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
            if due_for_print(now, next_print, previous, controller.state, controller.reason):
                publish(controller, joints, args.backend, decoder, stream, args.watch)
                next_print = now + 1 / args.print_rate
                previous = (controller.state, controller.reason)
            next_tick += 1 / args.rate
            delay = next_tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.monotonic()  # No burst of catch-up motion commands.
        controller.stop("program exit")
        publish(controller, controller.arm.read_joints(), args.backend, decoder,
                stream, args.watch)
        return 0
    finally:
        try:
            if arm is not None:
                arm.close()
        finally:
            # After close(), so the SDK's parting words go to the log too.
            stack.close()
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
    parser.add_argument("--mode", choices=("monitor", "teleop", "preflight", "probe-gripper"),
                        default="monitor")
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
    parser.add_argument("--watch", action="store_true",
                        help="print a one-line readout instead of the JSON record: the state, "
                             "and how far each joint still has to be turned to be in the arm's pose")
    parser.add_argument("--arm-log", type=Path, default=Path(DEFAULT_ARM_LOG),
                        help="where the vendor SDK's own console output goes, so it stays out "
                             "of the readout (hardware only)")
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
