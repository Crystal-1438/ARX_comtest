"""Decoder for the Leader_f103c8t6 USART3 feedback stream.

Wire spec: ``docs/uart_packet.md``. ASCII lines, 115200 8N1, 200 Hz:

    <J1>,<J2>,<J3>,<J4>,<J5>,<J6>,<J7>\\r\\n

J1..J6 are single-turn absolute angles in 0.1 degrees, or ``-1`` meaning "this
joint has never produced a sample". J7 is the gripper ADC. There is no
checksum and no sequence number, so the only corruption this decoder can catch
is a value that lands outside its documented range.

A calibrated map also gives this decoder the ``anchor`` hook: a single-turn
encoder cannot say which turn it is on, so the pose the arm is actually in picks
one, and the whole-turn bias that comes out of it is carried until the board
resets. ``app.py`` installs it as the controller's ``pre_arm`` check, so a
session where the leader and the arm are not in the same pose is refused instead
of jumping.

Load it with ``app.py --decoder leader_decoder.py``.
"""

import math
import re
import time

from leader_map import (
    ANCHOR_TOLERANCE_DEG, Mapper, load_mapping, resolve_mapping_path, shortest_turn,
)
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
        # The last anchor verdict, or None if this session has not been anchored
        # yet. Cleared wherever the unwrap origin moves -- a bias chosen against
        # the old origin means nothing against the new one.
        self.anchor_verdict = None

    @property
    def calibrated(self):
        return self.mapping.calibrated

    def anchor(self, arm_radians):
        """Choose the whole turn each encoder is on, from the pose the arm is in.

        The controller calls this just before enabling the arm -- it is
        installed as ``Controller.pre_arm`` -- so this is the moment both
        readings are on hand. Returns None to arm, or a reason not to.

        The one case with no answer is a session with no frame yet: there is
        nothing to bias, and the turn arithmetic would raise on it. That is
        refused in words like any other, because an exception here would unwind
        through the control loop's state transition and out of the program --
        pressing the key a moment too early must not kill the run.
        """
        needed_deg = [joint.from_arm_deg(math.degrees(angle))
                      for joint, angle in zip(self.mapping.joints, arm_radians)]
        if any(angle is None for angle in self.mapper.continuous):
            self.anchor_verdict = None
            return "no leader frame has arrived yet"
        verdict = self.mapper.anchor(needed_deg)
        self.anchor_verdict = verdict
        # Re-publish now rather than waiting for the next frame: the operator
        # has just asked to arm, and this is the answer. The frame is sticky, so
        # this repeats the last one with the verdict attached.
        self._publish(None)
        if verdict["ok"]:
            return None
        return self._anchor_refusal(verdict, needed_deg)

    def distance(self, arm_radians):
        """How far each joint has to be turned to be in the arm's pose, now.

        The same shortest-side distance the refusal is phrased in, so what the
        operator watches while moving the leader is the number the refusal will
        quote, and it reaches zero exactly when arming becomes possible.

        Read-only, deliberately: it must not choose the turn. That is `anchor`'s
        job alone, once, at the moment the arm is enabled -- a bias written while
        the leader is merely passing through would be carried into the session.

        None until a frame has arrived, which is the one case with no answer.
        """
        if any(angle is None for angle in self.mapper.continuous):
            return None
        needed_deg = [joint.from_arm_deg(math.degrees(angle))
                      for joint, angle in zip(self.mapping.joints, arm_radians)]
        turns = [shortest_turn(needed, now)
                 for now, needed in zip(self.mapper.continuous, needed_deg)]
        return {"turn_deg": turns,
                "outside": [index for index, turn in enumerate(turns)
                            if abs(turn) > ANCHOR_TOLERANCE_DEG],
                "tolerance_deg": ANCHOR_TOLERANCE_DEG}

    def _anchor_refusal(self, verdict, needed_deg):
        """Say which joints are not where the arm is, and how far to move them.

        Two numbers per joint again, and now they are the same size: the turn is
        the physical move the hand has to make, and the command is what the arm
        would be told if it were armed anyway. They differ only in sign. Leading
        with the turn is what the operator can act on; see shortest_turn.

        Both angles are given within one turn, which is the only way they can be
        looked up: ``continuous`` unwraps from wherever the stream started, so a
        joint the operator has turned past the rollover reads as -72.1 here
        while the board says 287.9 -- and 287.9 is the number in front of them.
        The verdict itself is unaffected, being a distance.
        """
        tolerance = verdict["tolerance_deg"]
        # Every joint that is out, not just the worst: they all have to be
        # moved, and naming one per attempt sends the operator round again.
        away, moves = [], []
        for index, joint in enumerate(self.mapping.joints):
            if abs(verdict["residual_deg"][index]) <= tolerance:
                continue
            now = self.mapper.continuous[index] % 360.0
            needed = needed_deg[index] % 360.0
            away.append(f"J{index + 1} reads {now:.1f} deg where the arm's pose "
                        f"calls for {needed:.1f} "
                        f"(turn it {shortest_turn(needed, now):+.1f} deg)")
            moves.append(f"J{index + 1} {joint.sign * verdict['residual_deg'][index]:+.1f} deg")
        return ("the leader and the arm are not in the same pose: " + "; ".join(away) +
                ". Arming here would move " + " and ".join(moves) +
                f" (tolerance {tolerance:.0f} deg). Hand-match the leader to the arm "
                "and press a again")

    def _restart_origin(self):
        """Re-anchor unwrapping, and drop the verdict that went with it.

        A new origin is exactly the thing the bias was chosen against, so this
        is the one place that moves it and the only place that has to clear both.
        """
        self.mapper.reset()
        self.anchor_verdict = None

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
        return self.mapper.to_radians([value / 10.0 for value in fields[:JOINTS]])

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
            # Held on the decoder rather than in the frame, so it survives the
            # blank rebuilds on loops that consumed no new bytes.
            "anchor": self.anchor_verdict,
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
        # The seventh field is the input the gripper follows, normalized here
        # because that is the only place that knows it arrived as an ADC out of
        # 1000. Zero is the open end, which is what the mapping is defined
        # against; the raw field stays under "gripper" in the telemetry above.
        return [Command("target", self.seq, newest[1], True,
                        newest[0][JOINTS] / GRIPPER_MAX)]


def create_decoder():
    return LeaderUartDecoder(load_mapping(resolve_mapping_path(__file__)))
