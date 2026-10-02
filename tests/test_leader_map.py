import json
import math
from pathlib import Path
import tempfile
import unittest

from leader_map import (ANCHOR_TOLERANCE_DEG, JOINTS, JointMap, LeaderMap, Mapper,
                        load_mapping, resolve_mapping_path, resolve_turns,
                        shortest_turn, uncalibrated)

EXAMPLE = Path(__file__).resolve().parents[1] / "leader_map.example.json"


def write(directory, config, name="leader_map.json"):
    path = Path(directory) / name
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def valid(**overrides):
    joint = {"sign": 1, "offset_deg": 0.0, "unwrap": True}
    joint.update(overrides)
    return {"calibrated": False, "joints": [dict(joint) for _ in range(JOINTS)]}


class ResolutionTests(unittest.TestCase):
    def test_explicit_beats_environment_beats_decoder_directory(self):
        environment = {"ARX_LEADER_MAP": "/from/env.json"}
        self.assertEqual(resolve_mapping_path("/somewhere/decoder.py", "/flagged.json", environment),
                         Path("/flagged.json"))
        self.assertEqual(resolve_mapping_path("/somewhere/decoder.py", None, environment),
                         Path("/from/env.json"))
        self.assertEqual(resolve_mapping_path("/somewhere/decoder.py", None, {}),
                         Path("/somewhere/leader_map.json"))

    def test_example_configuration_ships_uncalibrated(self):
        mapping = load_mapping(EXAMPLE)
        self.assertFalse(mapping.calibrated)
        self.assertEqual(len(mapping.joints), JOINTS)
        # The example has to stay loadable: it is the starting point people copy.
        self.assertEqual(len(mapping.reference_deg), JOINTS)

    def test_missing_file_yields_uncalibrated_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            mapping = load_mapping(Path(directory) / "absent.json")
        self.assertFalse(mapping.calibrated)
        self.assertEqual(mapping.joints, uncalibrated().joints)
        self.assertTrue(all(joint.unwrap for joint in mapping.joints))
        self.assertIsNone(mapping.reference_deg)


class ValidationTests(unittest.TestCase):
    def load(self, config):
        with tempfile.TemporaryDirectory() as directory:
            return load_mapping(write(directory, config))

    def reject(self, config):
        with self.assertRaises(ValueError):
            self.load(config)

    def test_accepts_a_calibrated_map(self):
        config = valid(offset_deg=-12.5)
        config["calibrated"] = True
        config["comment"] = "field notes"
        mapping = self.load(config)
        self.assertTrue(mapping.calibrated)
        self.assertEqual(mapping.joints[0].offset_deg, -12.5)

    def test_rejects_structural_damage(self):
        self.reject({"calibrated": "yes", "joints": [{}] * JOINTS})
        self.reject({"calibrated": False, "joints": [{}] * (JOINTS - 1)})
        self.reject({"calibrated": False, "joints": [{}] * (JOINTS + 1)})
        self.reject({"calibrated": False, "joints": "six"})
        self.reject({"calibrated": False, "joints": [{}] * JOINTS, "jionts": []})
        self.reject([{"calibrated": False}])

    def test_rejects_a_plausible_but_wrong_joint(self):
        # A bad sign or offset teleoperates the arm the wrong way; refusing to
        # start beats silently accepting it.
        for broken in ({"sign": 0}, {"sign": 2}, {"sign": -1.5}, {"sign": "1"},
                       {"offset_deg": None}, {"offset_deg": float("inf")},
                       {"offset_deg": "0"}, {"unwrap": 1}, {"unwrap": "true"},
                       {"siqn": 1}, {"sign": 1, "scale": 2}):
            with self.subTest(broken=broken):
                self.reject(valid(**broken))

    def test_accepts_the_reference_pose(self):
        config = valid()
        config["reference_deg"] = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]
        self.assertEqual(self.load(config).reference_deg[1], 328.1)

    def test_a_map_without_a_reference_is_still_loadable(self):
        # Maps written before the field existed, and hand-written ones, stay
        # valid: they simply cannot be checked at startup.
        self.assertIsNone(self.load(valid()).reference_deg)

    def test_rejects_a_reference_that_is_not_a_pose(self):
        # A raw angle exists only inside one turn of the encoder, so anything
        # outside that is a mix-up rather than a pose -- and accepting it would
        # make the startup check pass or fail for the wrong reason.
        for broken in ([0.0] * (JOINTS - 1), [0.0] * (JOINTS + 1), "0,0,0,0,0,0",
                       [0.0] * 5 + [None], [0.0] * 5 + [float("nan")],
                       [0.0] * 5 + [-0.1], [0.0] * 5 + [360.0]):
            with self.subTest(broken=broken):
                self.reject(dict(valid(), reference_deg=broken))


class ResolveTurnsTests(unittest.TestCase):
    """Which turn of the encoder each joint is on, as decided from the arm.

    The encoder gives one number per turn, so this is the step that has to
    choose; everything about a session's start pose being "wrong" came from not
    having it.
    """

    READ = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]

    def resolve(self, needed, read=None, **overrides):
        return resolve_turns(self.READ if read is None else read, needed, **overrides)

    def test_the_pose_it_already_reads_needs_no_turn(self):
        result = self.resolve(self.READ)
        self.assertTrue(result["ok"])
        self.assertEqual(result["turns_deg"], [0.0] * JOINTS)
        self.assertEqual(result["residual_deg"], [0.0] * JOINTS)

    def test_a_pose_on_the_far_side_of_the_rollover_is_not_hundreds_off(self):
        # The case this whole change is for: the leader sits at 4.0 where the
        # arm's pose corresponds to 354.0 -- ten degrees apart, but the literal
        # difference is -350. A whole turn of bias absorbs the wrap, so what is
        # left over is the ten degrees and the verdict is taken on that.
        read = [4.0, 328.1, 106.0, 235.3, 287.5, 208.5]
        needed = [354.0, 328.1, 106.0, 235.3, 287.5, 208.5]
        result = self.resolve(needed, read)
        self.assertTrue(result["ok"])
        self.assertEqual(result["turns_deg"][0], 360.0)
        self.assertAlmostEqual(result["residual_deg"][0], 10.0)

    def test_the_turn_it_picks_is_always_a_whole_number_of_turns(self):
        for shift in (0.0, 360.0, 720.0, -360.0):
            with self.subTest(shift=shift):
                result = self.resolve([value + shift for value in self.READ])
                self.assertTrue(result["ok"])
                for turn in result["turns_deg"]:
                    self.assertEqual(turn % 360.0, 0.0)

    def test_a_joint_further_than_the_tolerance_is_refused(self):
        needed = list(self.READ)
        needed[2] += ANCHOR_TOLERANCE_DEG + 1.0
        result = self.resolve(needed)
        self.assertFalse(result["ok"])
        self.assertEqual(result["worst_joint"], 2)

    def test_a_difference_right_at_the_tolerance_is_allowed(self):
        needed = list(self.READ)
        needed[0] += ANCHOR_TOLERANCE_DEG
        self.assertTrue(self.resolve(needed)["ok"])

    def test_the_residual_is_the_shortest_turn_the_other_way_round(self):
        # Two functions, one number. The verdict is what the arm would be
        # commanded and the turn is what the hand has to do, and if they ever
        # disagree the refusal message tells the operator to do one thing while
        # the arm does another. Checked across the rollover in both directions
        # and at the whole-turn boundaries, where the two are the same size and
        # may differ by exactly a turn.
        for offset in (-170.0, -90.0, -1.0, 0.0, 1.0, 90.0, 179.0, 180.0, 181.0):
            with self.subTest(offset=offset):
                needed = [value + offset for value in self.READ]
                result = self.resolve(needed)
                for index, now in enumerate(self.READ):
                    # Modulo a turn, folded into (-180, 180] so the comparison
                    # does not trip on the wrap itself.
                    apart = (result["residual_deg"][index]
                             + shortest_turn(needed[index], now))
                    self.assertAlmostEqual((apart + 180.0) % 360.0 - 180.0, 0.0, places=6)

    def test_the_residual_never_exceeds_half_a_turn(self):
        for offset in (-540.0, -359.0, 359.0, 540.0, 4000.0):
            with self.subTest(offset=offset):
                for residual in self.resolve([value + offset for value in self.READ])["residual_deg"]:
                    self.assertLessEqual(abs(residual), 180.0 + 1e-9)

    def test_a_joint_with_no_frame_yet_is_not_guessed(self):
        # run before any frame: there is no reading to bias, and inventing one
        # would arm the arm on a pose nobody has seen.
        with self.assertRaises(ValueError):
            self.resolve(self.READ, read=[None] + self.READ[1:])

    def test_refuses_angles_that_are_not_six_joints(self):
        with self.assertRaises(ValueError):
            self.resolve(self.READ[:5])


class ShortestTurnTests(unittest.TestCase):
    """The one-signed-angle form of the same distance ``resolve_turns`` reports.

    The verdict and this function answer different questions -- the residual is
    what the arm walks to meet the leader, the turn is how far the hand has to
    move to meet it -- but both are shortest-turn distances, and ``ResolveTurnsTests``
    pins them to each other. What is tested here is only the angle: single
    signed value, never more than half a turn, zero when the two agree.
    """

    def test_a_short_move_the_other_way_is_short(self):
        # 322.8 and 14.2 are 51.4 apart going down through zero, and 308.6 the
        # other way. The hand only ever has to travel the 51.4.
        self.assertAlmostEqual(shortest_turn(322.8, 14.2), -51.4, places=6)

    def test_it_is_the_short_way_round_the_rollover(self):
        # Ten degrees apart across the 0/360 seam, not 350: the encoder cannot
        # tell the two apart and neither may this.
        self.assertAlmostEqual(shortest_turn(354.0, 4.0), -10.0, places=6)
        self.assertAlmostEqual(shortest_turn(4.0, 354.0), 10.0, places=6)

    def test_no_turn_is_needed_where_the_pose_already_is(self):
        for angle in (0.0, 14.2, 359.9):
            with self.subTest(angle=angle):
                self.assertAlmostEqual(shortest_turn(angle, angle), 0.0, places=6)

    def test_the_turn_never_exceeds_half_a_turn(self):
        for now in (0.0, 1.0, 180.0, 359.0):
            for reference in (0.0, 90.0, 270.0, 359.0):
                with self.subTest(now=now, reference=reference):
                    self.assertLessEqual(abs(shortest_turn(reference, now)), 180.0 + 1e-9)


class MapperTests(unittest.TestCase):
    def mapper(self, **overrides):
        return Mapper(LeaderMap(joints=(JointMap(**overrides),) * JOINTS, calibrated=True))

    def test_identity_placeholder_still_reports_degrees_as_radians(self):
        radians = Mapper(uncalibrated()).to_radians([100.0] * JOINTS)
        self.assertAlmostEqual(radians[0], math.radians(100.0))

    def test_sign_and_offset(self):
        radians = self.mapper(sign=-1, offset_deg=90.0).to_radians([30.0] * JOINTS)
        self.assertAlmostEqual(radians[0], math.radians(60.0))

    def test_single_turn_rollover_does_not_look_like_a_full_revolution(self):
        mapper = self.mapper()
        self.assertAlmostEqual(mapper.to_radians([355.0] * JOINTS)[0], math.radians(355.0))
        self.assertAlmostEqual(mapper.to_radians([5.0] * JOINTS)[0], math.radians(365.0))
        self.assertAlmostEqual(mapper.to_radians([355.0] * JOINTS)[0], math.radians(355.0))

    def test_unwrap_can_be_disabled_for_a_single_turn_joint(self):
        mapper = self.mapper(unwrap=False)
        mapper.to_radians([355.0] * JOINTS)
        self.assertAlmostEqual(mapper.to_radians([5.0] * JOINTS)[0], math.radians(5.0))

    def test_reset_reanchors_the_unwrapped_origin(self):
        mapper = self.mapper()
        mapper.to_radians([355.0] * JOINTS)
        mapper.reset()
        self.assertAlmostEqual(mapper.to_radians([5.0] * JOINTS)[0], math.radians(5.0))

    def test_from_arm_deg_inverts_the_mapping(self):
        for sign in (1.0, -1.0):
            for offset in (0.0, 90.0, -75.5):
                with self.subTest(sign=sign, offset=offset):
                    joint = JointMap(sign=sign, offset_deg=offset)
                    self.assertAlmostEqual(
                        sign * joint.from_arm_deg(30.0) + offset, 30.0)


class AnchorTests(unittest.TestCase):
    """Fixing the whole turn from the arm's pose, and carrying it after that."""

    READ = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]

    def mapper(self):
        return Mapper(LeaderMap(joints=(JointMap(),) * JOINTS, calibrated=True))

    def anchored(self, mapper=None):
        mapper = mapper or self.mapper()
        mapper.to_radians(self.READ)
        return mapper, mapper.anchor(self.READ)

    def test_an_unanchored_mapper_is_the_plain_mapping(self):
        mapper = self.mapper()
        self.assertEqual(mapper.bias, [0.0] * JOINTS)
        self.assertAlmostEqual(mapper.to_radians([100.0] * JOINTS)[0], math.radians(100.0))

    def test_anchoring_a_pose_that_matches_changes_nothing(self):
        mapper, verdict = self.anchored()
        self.assertTrue(verdict["ok"])
        self.assertEqual(mapper.bias, [0.0] * JOINTS)
        self.assertAlmostEqual(mapper.to_radians([100.0] * JOINTS)[0], math.radians(100.0))

    def test_the_bias_carries_the_stream_past_the_rollover(self):
        # The session starts reading 4.0 where the arm's pose calls for 354.0. Without
        # the bias the next sample, 5.0, maps to 5.0 and the arm is commanded
        # -349 from where it should be; with it, the stream continues from 364.
        mapper = self.mapper()
        mapper.to_radians([4.0] * JOINTS)
        self.assertTrue(mapper.anchor([354.0] * JOINTS)["ok"])
        self.assertAlmostEqual(mapper.to_radians([5.0] * JOINTS)[0], math.radians(365.0))

    def test_the_bias_leaves_the_unwrapped_reading_alone(self):
        # ``continuous`` is what the calibration tool samples and what the wire
        # is compared against; the bias is a separate term.
        mapper, _ = self.anchored()
        mapper.to_radians([5.0] * JOINTS)
        self.assertAlmostEqual(mapper.continuous[0], 5.0)

    def test_a_refused_anchor_writes_no_bias(self):
        mapper = self.mapper()
        mapper.to_radians(self.READ)
        verdict = mapper.anchor([value + 90.0 for value in self.READ])
        self.assertFalse(verdict["ok"])
        self.assertEqual(mapper.bias, [0.0] * JOINTS)

    def test_a_refusal_does_not_disturb_an_earlier_bias(self):
        mapper = self.mapper()
        mapper.to_radians(self.READ)
        mapper.anchor([value + 360.0 for value in self.READ])
        self.assertEqual(mapper.bias, [360.0] * JOINTS)
        self.assertFalse(mapper.anchor([value + 90.0 for value in self.READ])["ok"])
        self.assertEqual(mapper.bias, [360.0] * JOINTS)

    def test_reset_takes_the_bias_with_it(self):
        # The bias was chosen against an origin that no longer exists, so
        # carrying it over would be a mapping nobody has checked.
        mapper = self.mapper()
        mapper.to_radians(self.READ)
        mapper.anchor([value + 360.0 for value in self.READ])
        mapper.reset()
        self.assertEqual(mapper.bias, [0.0] * JOINTS)
        self.assertAlmostEqual(mapper.to_radians([5.0] * JOINTS)[0], math.radians(5.0))

    def test_anchoring_before_any_frame_raises(self):
        with self.assertRaises(ValueError):
            self.mapper().anchor([0.0] * JOINTS)


if __name__ == "__main__":
    unittest.main()
