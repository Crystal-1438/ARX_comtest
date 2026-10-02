"""The ADRC reference's standalone tracking differentiator, one per joint.

``TDFunction_independent`` in ``ref/adrc.c`` advances a two-state trajectory that
approaches a reference as fast as an acceleration bound ``r`` allows, carrying
the derivative along with it. That function is all of the reference that is used
here; the non-linear feedback and the extended state observer wrapped around it
belong to a closed servo loop, which is not what a position command handed to
the vendor's own joint loop is.

Two things about the way it is used here are worth stating once.

* The angles are **multi-turn**. The leader's encoder reports one number per
  turn, and the mapper unwraps it into a continuous angle that is never folded
  back into 0..360 or +/-180. Feeding a folded angle in would make every pass
  through the rollover look like a step of a whole turn, and the trajectory
  would swing to chase a move that never happened. Nothing here wraps.
* Everything is in degrees, because ``r`` is given in degrees per second
  squared. ``Limits`` holds joint angles in radians everywhere else, so the
  conversion happens exactly where the trajectory is handed over, one line on
  each side.
"""

import math

JOINTS = 6
# ref/adrc.h's tuning guide: ``h`` is the control period, and ``h0`` ("滤波因子")
# is twice it. The period is this loop's own measured step, so h0 moves with it.
H0_FACTOR = 2.0


def _sign(value):
    return (value > 0) - (value < 0)


def _fsg(value, d):
    """ref/adrc.c ``fsg``: 1 inside the linear region (|value| < d), 0 outside."""
    return (_sign(value + d) - _sign(value - d)) / 2


def fst(delta, velocity, r, h0):
    """ref/adrc.c ``fst``: the acceleration that closes ``delta`` fastest.

    Transcribed term for term from the reference (``adrc.c:81``). ``delta`` is
    the remaining error, ``velocity`` the current derivative of the trajectory,
    ``r`` the acceleration bound and ``h0`` the filter factor; the result is an
    acceleration in the same unit as ``r``. Far from the reference it is the
    bound itself, with the sign that turns the trajectory around; inside the
    ``d``-wide band it becomes linear, which is what keeps the discrete step
    from chattering around the target.
    """
    d = r * h0 * h0
    a0 = h0 * velocity
    y = delta + a0
    a1 = math.sqrt(d * (d + 8.0 * abs(y)))
    a2 = a0 + _sign(y) * (a1 - d) / 2.0
    near_y = _fsg(y, d)
    a = (a0 + y) * near_y + a2 * (1.0 - near_y)
    near_a = _fsg(a, d)
    return -r * (a / d) * near_a - r * _sign(a) * (1.0 - near_a)


def _bounded(value, limit):
    return min(max(value, -limit), limit)


class Tracker:
    """One tracking differentiator per joint, in degrees, fed multi-turn angles.

    The state is the commanded trajectory itself: ``step`` returns the joint
    angles to send, so the arm is never asked for a point the differentiator did
    not produce, and the state cannot drift away from what was written.
    """

    def __init__(self, joints=JOINTS):
        self.joints = joints
        self.angle = (0.0,) * joints
        self.rate = (0.0,) * joints

    def reset(self, angles_deg):
        """Start at ``angles_deg``, standing still.

        Called when the arm is enabled, with the measured pose: zero velocity
        because the arm is not moving yet, and at the measured angle because
        anything else would be an uncommanded step on the first tick.
        """
        if len(angles_deg) != self.joints:
            raise ValueError(f"expected {self.joints} angles")
        self.angle = tuple(float(angle) for angle in angles_deg)
        self.rate = (0.0,) * self.joints

    def step(self, targets_deg, r_deg, dt, speed_limit_deg):
        """Advance by ``dt`` seconds toward ``targets_deg`` and return the angles.

        ``r_deg`` is per joint, in degrees per second squared, and
        ``speed_limit_deg`` caps the commanded rate -- the differentiator bounds
        acceleration, not speed, so without it a large step would ask for a rate
        the arm cannot track. Both bounds are in the same degrees the angles are.
        """
        if len(targets_deg) != self.joints:
            raise ValueError(f"expected {self.joints} targets")
        if dt <= 0.0:
            return self.angle  # Nothing to integrate; not an error.
        h0 = H0_FACTOR * dt
        angle = []
        rate = []
        for index in range(self.joints):
            accel = fst(self.angle[index] - targets_deg[index], self.rate[index],
                        r_deg[index], h0)
            velocity = _bounded(self.rate[index] + dt * accel, speed_limit_deg)
            rate.append(velocity)
            angle.append(self.angle[index] + dt * velocity)
        self.angle = tuple(angle)
        self.rate = tuple(rate)
        return self.angle
