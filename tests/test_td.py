import math
import unittest

from td import Tracker, fst

# The six values the joints are tuned with, in the reference's unit: degrees per
# second squared.
R_DEG = (400.0, 500.0, 600.0, 4000.0, 1000.0, 4000.0)
SPEED_LIMIT_DEG = math.degrees(2.0)


class FstTests(unittest.TestCase):
    """``fst`` is a transcription of ``ref/adrc.c``, so it is pinned by the
    properties the transcription has to keep rather than by re-deriving the
    same arithmetic a second time."""

    def test_far_from_the_reference_it_is_the_acceleration_bound(self):
        self.assertEqual(fst(-100.0, 0.0, 400.0, 0.02), 400.0)
        self.assertEqual(fst(100.0, 0.0, 400.0, 0.02), -400.0)
        self.assertEqual(fst(-100.0, 0.0, 4000.0, 0.02), 4000.0)

    def test_at_the_reference_and_at_rest_it_asks_for_nothing(self):
        self.assertTrue(abs(fst(0.0, 0.0, 400.0, 0.02)) < 1e-9)

    def test_it_never_asks_for_more_than_the_bound(self):
        for r in R_DEG:
            for h0 in (0.002, 0.02, 0.1):
                for delta in (-300.0, -10.0, -0.5, -0.01, 0.0, 0.01, 0.5, 10.0, 300.0):
                    for velocity in (-200.0, -10.0, 0.0, 10.0, 200.0):
                        with self.subTest(r=r, h0=h0, delta=delta, velocity=velocity):
                            self.assertLessEqual(abs(fst(delta, velocity, r, h0)), r + 1e-9)

    def test_standing_still_it_pushes_back_toward_the_reference(self):
        # ``delta`` is v1 - ref, so the acceleration that closes it points the
        # other way: positive delta (ahead of the reference) is braked.
        for delta in (-300.0, -10.0, -0.5, 0.5, 10.0, 300.0):
            with self.subTest(delta=delta):
                self.assertEqual(math.copysign(1.0, fst(delta, 0.0, 400.0, 0.02)),
                                 -math.copysign(1.0, delta))


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = Tracker()

    def test_a_step_is_approached_without_passing_it(self):
        # This is the property the control loop leans on: the target is clamped
        # into the envelope, so a trajectory that never passes it never commands
        # a point outside either.
        for r in R_DEG:
            for dt in (0.001, 0.005, 0.01, 0.02, 0.05):
                for step in (0.5, 5.0, 30.0, 90.0, 359.0):
                    with self.subTest(r=r, dt=dt, step=step):
                        tracker = Tracker(1)
                        tracker.reset((0.0,))
                        for _ in range(int(8.0 / dt)):
                            angle = tracker.step((step,), (r,), dt, SPEED_LIMIT_DEG)[0]
                            self.assertLessEqual(angle, step + 1e-9)

    def test_it_arrives_and_stays(self):
        for r, step in zip(R_DEG, (30.0, -30.0, 90.0, 5.0, -180.0, 20.0)):
            with self.subTest(r=r, step=step):
                tracker = Tracker(1)
                tracker.reset((0.0,))
                for _ in range(800):
                    tracker.step((step,), (r,), 0.01, SPEED_LIMIT_DEG)
                self.assertAlmostEqual(tracker.angle[0], step, places=9)
                self.assertAlmostEqual(tracker.rate[0], 0.0, places=9)

    def test_the_rate_is_capped(self):
        tracker = Tracker(1)
        tracker.reset((0.0,))
        for _ in range(2000):
            tracker.step((359.0,), (4000.0,), 0.01, SPEED_LIMIT_DEG)
            self.assertLessEqual(abs(tracker.rate[0]), SPEED_LIMIT_DEG + 1e-9)

    def test_the_bound_is_per_joint(self):
        # J4 is tuned four thousand at most, J1 four hundred: given the same
        # step, the loosely bounded joint is the one that has moved further.
        tracker = Tracker()
        tracker.reset((0.0,) * 6)
        angles = tracker.step((30.0,) * 6, R_DEG, 0.01, SPEED_LIMIT_DEG)
        self.assertGreater(angles[3], angles[0])
        self.assertGreater(angles[5], angles[2])
        self.assertEqual(angles[3], angles[5])

    def test_a_multi_turn_angle_is_not_wrapped(self):
        # The leader's angle is unwrapped by the mapper and can sit past a whole
        # turn. Folded back into one, the step from 350 to 370 would look like
        # 350 -> 10 and the trajectory would swing a whole turn the wrong way.
        tracker = Tracker(1)
        tracker.reset((350.0,))
        angles = [tracker.step((370.0,), (400.0,), 0.01, SPEED_LIMIT_DEG)[0]
                  for _ in range(400)]
        self.assertTrue(all(a <= b + 1e-12 for a, b in zip(angles, angles[1:])))
        self.assertGreater(angles[0], 350.0)
        # It walks through the rollover rather than jumping a whole turn to it.
        self.assertTrue(any(359.0 < angle < 361.0 for angle in angles))
        self.assertLess(max(b - a for a, b in zip(angles, angles[1:])), 1.0)
        self.assertAlmostEqual(angles[-1], 370.0, places=9)

    def test_angles_far_past_a_turn_are_ordinary_numbers(self):
        tracker = Tracker(1)
        tracker.reset((700.0,))
        for _ in range(800):
            tracker.step((730.0,), (400.0,), 0.01, SPEED_LIMIT_DEG)
        self.assertAlmostEqual(tracker.angle[0], 730.0, places=9)

    def test_reset_starts_at_rest(self):
        self.tracker.reset((1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
        self.assertEqual(self.tracker.angle, (1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
        self.assertEqual(self.tracker.rate, (0.0,) * 6)

    def test_a_zero_or_negative_step_is_not_an_error(self):
        # ``dt`` comes from the wall clock, and two ticks in the same instant
        # are not a fault here; they simply integrate nothing.
        self.tracker.reset((1.0,) * 6)
        for dt in (0.0, -0.5):
            self.assertEqual(self.tracker.step((2.0,) * 6, R_DEG, dt, SPEED_LIMIT_DEG),
                             (1.0,) * 6)

    def test_it_refuses_a_ragged_pose(self):
        with self.assertRaises(ValueError):
            self.tracker.reset((1.0, 2.0))
        with self.assertRaises(ValueError):
            self.tracker.step((1.0, 2.0), R_DEG, 0.01, SPEED_LIMIT_DEG)


if __name__ == "__main__":
    unittest.main()
