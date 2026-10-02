"""Replaceable wire decoder. JSON lines are a bench-test protocol, not hardware spec."""

from dataclasses import dataclass
import json
import math


class ProtocolError(ValueError):
    pass


def vector6(value):
    if not isinstance(value, (list, tuple)) or len(value) != 6:
        raise ProtocolError("joints must contain exactly six numbers")
    try:
        valid = all(type(v) in (int, float) and math.isfinite(v) for v in value)
    except OverflowError:
        valid = False
    if not valid:
        raise ProtocolError("joints must be finite numbers (radians)")
    return tuple(float(v) for v in value)


@dataclass(frozen=True)
class Command:
    kind: str
    seq: int
    joints: tuple = ()
    deadman: bool = False
    # The teleoperation input for the gripper, normalized: 0.0 fully open, 1.0
    # fully closed. Deliberately not the number the leader's frame carries --
    # that one is a raw ADC and the decoder's telemetry keeps it under
    # "gripper". None means the sender has no gripper channel, which is inert:
    # nothing is sent to the arm's gripper at all.
    gripper_input: float = None

    def validate(self):
        if self.kind not in ("stop", "arm", "target"):
            raise ProtocolError("unknown command")
        if type(self.seq) is not int or not 0 <= self.seq < 2**63:
            raise ProtocolError("seq must be a non-negative 63-bit integer")
        if type(self.deadman) is not bool:
            raise ProtocolError("deadman must be boolean")
        if self.kind == "target":
            vector6(self.joints)
        elif self.joints:
            raise ProtocolError("only target commands may contain joints")
        if self.gripper_input is not None:
            if self.kind != "target":
                raise ProtocolError("only target commands may contain a gripper value")
            if (type(self.gripper_input) not in (int, float)
                    or not math.isfinite(self.gripper_input)):
                raise ProtocolError("gripper must be a finite number (0 open, 1 closed)")
            if not 0.0 <= self.gripper_input <= 1.0:
                raise ProtocolError("gripper must be within 0..1 (0 fully open, 1 closed)")
        return self


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("duplicate JSON key")
        result[key] = value
    return result


class JsonLineDecoder:
    """feed(bytes) -> list[Command]; errors must not yield a partial batch."""

    def __init__(self, max_frame_bytes=1024):
        self.buffer = bytearray()
        self.max_frame_bytes = max_frame_bytes

    def feed(self, data):
        self.buffer.extend(data)
        commands = []
        try:
            while b"\n" in self.buffer:
                line, _, rest = self.buffer.partition(b"\n")
                self.buffer = bytearray(rest)
                if len(line) > self.max_frame_bytes:
                    raise ProtocolError("frame too long")
                if not line.strip():
                    continue
                obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_keys)
                if not isinstance(obj, dict):
                    raise ProtocolError("frame must be an object")
                if set(obj) - {"v", "seq", "type", "joints", "deadman", "gripper"}:
                    raise ProtocolError("unknown frame fields")
                if type(obj.get("v")) is not int or obj["v"] != 1:
                    raise ProtocolError("expected protocol v=1")
                commands.append(Command(
                    obj.get("type"), obj.get("seq"),
                    vector6(obj["joints"]) if "joints" in obj else (),
                    obj.get("deadman", False),
                    obj.get("gripper"),
                ).validate())
            if len(self.buffer) > self.max_frame_bytes:
                raise ProtocolError("unterminated frame too long")
            return commands
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            self.buffer.clear()
            raise ProtocolError(str(exc)) from exc


def create_decoder():
    return JsonLineDecoder()
