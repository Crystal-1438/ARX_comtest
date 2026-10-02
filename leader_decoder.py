"""Decoder for the Leader_f103c8t6 USART3 feedback stream.

Wire spec: ``docs/uart_packet.md``. ASCII lines, 115200 8N1, 200 Hz:

    <J1>,<J2>,<J3>,<J4>,<J5>,<J6>,<J7>\\r\\n

J1..J6 are single-turn absolute angles in 0.1 degrees, or ``-1`` meaning "this
joint has never produced a sample". J7 is the gripper ADC. There is no
checksum and no sequence number, so the only corruption this decoder can catch
is a value that lands outside its documented range.

A calibrated map also lets this decoder check that a session started at the
pose the map was measured at, since its unwrapping origin is the first frame.
``app.py`` refuses to arm until that check passes or proves it cannot run.

Load it with ``app.py --decoder leader_decoder.py``.
"""

import re
import time

from leader_map import Mapper, check_reference, load_mapping, resolve_mapping_path
from protocol import Command, ProtocolError

FIELD_COUNT = 7
JOINTS = 6
ANGLE_MAX = 3599
GRIPPER_MAX = 1000
NO_DATA = -1

# Sent once every time the board resets (docs/uart_packet.md section 4). It is
# not a packet, but it is the only signal that the encoders are starting over.
HANDSHAKE = b"0123456789"

# Match the whole field: int() alone would quietly accept b" 12" and b"+12",
# which are exactly the shapes a flipped or inserted byte produces.
_INTEGER = re.compile(rb"-?[0-9]+")


def parse_line(line):
    """Return the seven raw fields, or None if the line is not a well-formed packet.

    None covers any partial or garbled line, matching the documented "field
    count must be exactly 7 or drop it" rule. The power-on handshake is
    intercepted before it reaches here, so it never counts as corruption.
    """
    parts = line.split(b",")
    if len(parts) != FIELD_COUNT:
        return None
    if any(_INTEGER.fullmatch(part) is None for part in parts):
        return None
    return tuple(int(part) for part in parts)


class LeaderUartDecoder:
    """feed(bytes) -> list[Command].

    Returns at most one command per call: the newest frame. The stream runs at
    200 Hz against a slower control loop, so older frames in the same batch
    would only add latency. Every *complete* line in the batch is still checked
    first, so a bad frame cannot hide behind a good one that follows it.
    """

    # The wire carries no arm/stop; those come from --operator-keys.
    provides_arm = False

    def __init__(self, mapping, max_frame_bytes=1024):
        self.mapping = mapping
        self.max_frame_bytes = max_frame_bytes
        self.buffer = bytearray()
        # seq counts commands handed to the controller, which is a batch at a
        # time; frames counts packets actually received. They differ by however
        # many frames arrived between control loop iterations, and the wire has
        # no sequence number, so a packet rate is the only way to notice loss.
        self.seq = 0
        self.frames = 0
        self.dropped = 0
        self.no_data = 0
        self.resets = 0
        # Documents section 4: the first packets after a board reset can still
        # carry -1 while the encoder waits for its first PWM period. That is a
        # startup transient, not a fault -- but only until a full frame lands.
        self.saw_valid = False
        self.last_frame = None
        self.last_telemetry = None
        self.mapper = Mapper(mapping)
        # Verdict on the frame the mapper unwraps from, and whether one is still
        # owed: every new origin needs its own verdict, so this is re-armed
        # wherever the origin moves. See startup_blocker.
        self.reference = None
        self.reference_pending = True

    @property
    def calibrated(self):
        return self.mapping.calibrated

    @property
    def startup_blocker(self):
        """Why the arm must not be armed yet, or None to allow it.

        The mapper's origin comes from the first frame it sees, so a session
        that began away from the calibrated pose cannot be corrected from here:
        the answer is to stop and start again with the leader where it belongs.

        Arming before any frame has arrived is refused too -- there is nothing
        to judge yet, and allowing it would leave the gate open to whoever
        presses the key first.
        """
        if self.reference is None:
            return "no leader frame has arrived yet"
        if not self.reference.get("checked") or self.reference["ok"]:
            return None
        return (f"the leader started {self.reference['worst_deg']:+.1f} deg from the "
                f"calibrated pose (J{self.reference['worst_joint'] + 1}, tolerance "
                f"{self.reference['tolerance_deg']:.0f} deg); put the leader back in "
                f"that pose and restart")

    def _restart_origin(self):
        """Re-anchor unwrapping, and ask for a fresh reference verdict.

        A new origin is exactly the thing that has to be judged again, so this
        is the one place that moves it.
        """
        self.mapper.reset()
        self.reference_pending = True

    def reset(self):
        """Drop the half-line and the unwrap history after an upstream reset.

        SerialInput discards its own buffer on backlog, and the controller
        faults on protocol errors; without this the next bytes would be spliced
        onto a stale fragment.

        Deliberately keeps ``saw_valid``: a dead encoder must go on faulting
        after a reset rather than being reclassified as a startup transient.
        The board announces its own reset with HANDSHAKE instead.
        """
        self.buffer.clear()
        self._restart_origin()

    def judge_reference(self, degrees):
        """Compare the first frame with the calibrated pose, if the map has one."""
        if self.mapping.reference_deg is None:
            return {"checked": False, "why": "the map records no reference_deg"}
        return check_reference(self.mapping.reference_deg, degrees)

    def _decode(self, fields):
        """Validate one packet. Returns radians, or None if the frame must be dropped."""
        gripper = fields[JOINTS]
        if not 0 <= gripper <= GRIPPER_MAX:
            raise ProtocolError(f"gripper field {gripper} outside 0..{GRIPPER_MAX}")
        missing = []
        for index, value in enumerate(fields[:JOINTS]):
            if value == NO_DATA:
                missing.append(index)
            elif not 0 <= value <= ANGLE_MAX:
                raise ProtocolError(f"J{index + 1} field {value} outside 0..{ANGLE_MAX}")
        if missing:
            names = ", ".join(f"J{index + 1}" for index in missing)
            if self.saw_valid:
                raise ProtocolError(f"encoders reported no data: {names}")
            self.no_data += 1
            return None
        self.saw_valid = True
        degrees = [value / 10.0 for value in fields[:JOINTS]]
        if self.reference_pending:
            # This frame is the one the mapper will unwrap from, so this is the
            # last moment its distance from the calibrated pose can be measured.
            self.reference_pending = False
            self.reference = self.judge_reference(degrees)
        return self.mapper.to_radians(degrees)

    def _publish(self, newest, error=None):
        """Record what the decoder last made of its input.

        The frame is sticky: print rate is lower than the stream rate, so about
        half of all reports land on a loop that consumed no new bytes, and a
        blank frame on those would make a healthy stream look dead. Freshness is
        carried by the stamp instead -- an unchanged stamp means the values on
        screen are stale.
        """
        if newest is not None:
            fields, radians = newest
            self.last_frame = {
                "seq": self.seq,
                "fields": list(fields),
                "angle_deg": [value / 10.0 for value in fields[:JOINTS]],
                "gripper": fields[JOINTS],
                "target_rad": list(radians),
                "host_monotonic": time.monotonic(),
            }
        telemetry = {
            "map_source": self.mapping.source,
            "calibrated": self.calibrated,
            "frames": self.frames,
            "dropped": self.dropped,
            "no_data": self.no_data,
            "resets": self.resets,
            "reference": self.reference,
            "frame": self.last_frame,
        }
        if error is not None:
            telemetry["error"] = error
        self.last_telemetry = telemetry

    def feed(self, data):
        self.buffer.extend(data)
        newest = None
        try:
            while b"\n" in self.buffer:
                line, _, rest = self.buffer.partition(b"\n")
                self.buffer = bytearray(rest)
                line = line.rstrip(b"\r")
                if len(line) > self.max_frame_bytes:
                    raise ProtocolError("frame too long")
                if not line:
                    continue
                if line == HANDSHAKE:
                    self.resets += 1
                    self.saw_valid = False
                    self._restart_origin()
                    continue
                fields = parse_line(line)
                if fields is None:
                    self.dropped += 1
                    continue
                radians = self._decode(fields)
                if radians is not None:
                    self.frames += 1
                    newest = (fields, radians)
            if len(self.buffer) > self.max_frame_bytes:
                raise ProtocolError("unterminated frame too long")
        except ProtocolError as exc:
            self.buffer.clear()
            self._restart_origin()
            # Publish the counters even on the failing batch: this is the last
            # thing the operator sees before the arm latches FAULT.
            self._publish(None, error=str(exc))
            raise

        if newest is None:
            # Deliberately emit nothing rather than repeating the last target:
            # the controller's watchdog must still see a stalled stream.
            self._publish(None)
            return []
        self.seq += 1
        self._publish(newest)
        return [Command("target", self.seq, newest[1], True)]


def create_decoder():
    return LeaderUartDecoder(load_mapping(resolve_mapping_path(__file__)))
