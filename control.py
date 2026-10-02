"""Hardware-independent joint control and latched command timeout handling."""

from dataclasses import dataclass
import math

from protocol import Command, ProtocolError, vector6


@dataclass(frozen=True)
class Limits:
    lower: tuple
    upper: tuple
    max_speed: float = 0.2
    max_following_error: float = 0.15
    timeout: float = 0.25

    def __post_init__(self):
        vector6(self.lower)
        vector6(self.upper)
        if any(lo >= hi for lo, hi in zip(self.lower, self.upper)):
            raise ValueError("each lower joint limit must be below upper")
        for value in (self.max_speed, self.max_following_error, self.timeout):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("speed, following error and timeout must be positive")

    def check(self, joints):
        joints = vector6(joints)
        if any(not lo <= q <= hi for q, lo, hi in zip(joints, self.lower, self.upper)):
            raise ProtocolError("joint position outside configured limits")
        return joints


class Controller:
    def __init__(self, arm, limits, now):
        self.arm = arm
        self.limits = limits
        self.state = "STOPPED"
        self.reason = "startup"
        self.last_seq = -1
        self.last_input = now
        self.last_tick = now
        self.target = None
        self.commanded = None
        # Optional veto on enabling the arm, called with the measured joints.
        # Returning a reason refuses the arm and shows the reason; returning
        # None allows it. It belongs to the caller -- nothing here knows what
        # would make a decoder want to refuse -- but it has to be *here* rather
        # than at either entry point, because ARM arrives both from the wire
        # (handle) and from the operator's key (operator_arm) and the two must
        # not be able to disagree about whether the session is safe to enable.
        self.pre_arm = None
        self.arm.stop()

    def stop(self, reason, fault=False):
        # Clear the command even if the physical stop raises an exception.
        self.state = "FAULT" if fault else "STOPPED"
        self.reason = reason
        self.target = self.commanded = None
        self.arm.stop()

    def _apply(self, kind, joints, now):
        """State transitions shared by the wire path and the local operator path."""
        if self.state == "FAULT":
            return  # Explicit STOP followed by ARM is required after a fault.
        if kind == "arm":
            if self.state != "STOPPED":
                return  # Repeated ARM frames cannot refresh the target watchdog.
            # Read once and hand it on: the veto and the position the arm is
            # started from have to be the same sample, or the check could pass
            # on one reading and the arm be enabled at another.
            measured = self.limits.check(self.arm.read_joints())
            if self.pre_arm is not None:
                blocker = self.pre_arm(measured)
                if blocker:
                    self.stop(f"refusing to arm: {blocker}")
                    return
            self.commanded = self.target = measured
            self.arm.start(measured)
            self.state = "ACTIVE"
            self.reason = "armed at measured position"
            self.last_input = self.last_tick = now
        elif self.state == "ACTIVE":
            self.target = self.limits.check(joints)
            self.last_input = now

    def handle(self, command, now):
        if not isinstance(command, Command):
            raise ProtocolError("decoder must return Command objects")
        command.validate()
        # A STOP is always honored, including after a controller sequence reset.
        if command.kind == "stop":
            self.last_seq = max(self.last_seq, command.seq)
            self.stop("operator stop")
            return
        if command.seq <= self.last_seq:
            raise ProtocolError("replayed/out-of-order sequence; restart sender and receiver together")
        self.last_seq = command.seq
        if not command.deadman:
            self.stop("deadman released")
            return
        self._apply(command.kind, command.joints, now)

    def operator_stop(self, reason="operator stop"):
        """Local STOP. Clears a latched FAULT, and never touches the wire sequence."""
        self.stop(reason)

    def operator_arm(self, now):
        """Local ARM, exempt from the wire sequence.

        A decoder for a wire format that carries no arm/stop -- the leader
        board's, for instance -- can never enable the arm and can never clear a
        latched fault on its own. This is that missing channel. It leaves
        last_seq alone, so an operator action can neither collide with nor
        consume a decoder's own numbering.
        """
        self._apply("arm", (), now)

    def watchdog(self, now):
        # Call before processing newly arrived input so late packets cannot revive motion.
        if self.state == "ACTIVE" and now - self.last_input >= self.limits.timeout:
            self.stop("serial command timeout", fault=True)

    def tick(self, now):
        self.watchdog(now)
        dt = now - self.last_tick
        self.last_tick = now
        feedback = vector6(self.arm.read_joints())
        if self.state != "ACTIVE":
            return feedback
        if dt < 0 or dt >= self.limits.timeout:
            self.stop("control loop timing fault", fault=True)
            return feedback
        self.limits.check(feedback)
        if any(abs(q - actual) > self.limits.max_following_error
               for q, actual in zip(self.commanded, feedback)):
            self.stop("joint following error", fault=True)
            return feedback
        step = self.limits.max_speed * dt
        self.commanded = tuple(
            q + max(-step, min(step, target - q))
            for q, target in zip(self.commanded, self.target)
        )
        self.arm.write_joints(self.commanded)
        return feedback
