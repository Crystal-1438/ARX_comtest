import json
import math
from pathlib import Path
import tempfile
import unittest

from leader_map import (JOINTS, JointMap, LeaderMap, Mapper,
                        REFERENCE_TOLERANCE_DEG, check_reference, load_mapping,
                        resolve_mapping_path, shortest_turn, uncalibrated)

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


class ReferenceTests(unittest.TestCase):
    """The map is only true at the pose it was measured at, and this is the
    check that a session started there."""

    REFERENCE = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]

    def check(self, raw, reference=None):
        return check_reference(self.REFERENCE if reference is None else reference, raw)

    def test_the_reference_pose_itself_is_accepted(self):
        result = self.check(self.REFERENCE)
        self.assertTrue(result["ok"])
        self.assertEqual(result["offsets_deg"], [0.0] * JOINTS)

    def test_a_small_hand_placement_error_is_accepted(self):
        raw = [value + 1.0 for value in self.REFERENCE]
        self.assertTrue(self.check(raw)["ok"])

    def test_the_offset_it_reports_is_the_walk_the_arm_would_make(self):
        raw = list(self.REFERENCE)
        raw[2] += 90.0
        result = self.check(raw)
        self.assertFalse(result["ok"])
        self.assertEqual(result["worst_joint"], 2)
        self.assertAlmostEqual(result["worst_deg"], 90.0)

    def test_a_difference_just_over_the_tolerance_fails(self):
        raw = list(self.REFERENCE)
        raw[0] += REFERENCE_TOLERANCE_DEG + 0.5
        self.assertFalse(self.check(raw)["ok"])

    def test_the_wrap_is_not_a_small_step(self):
        # Ten degrees past the reference on the far side of 0/360 reads as 350
        # away, and 350 is what the mapper would command: it takes this first
        # frame as its origin, so there is no history to unwrap against yet.
        # Shortest-path arithmetic here would wave the session through.
        result = self.check([4.0, 328.1, 106.0, 235.3, 287.5, 208.5],
                            reference=[354.0, 328.1, 106.0, 235.3, 287.5, 208.5])
        self.assertFalse(result["ok"])
        self.assertAlmostEqual(result["worst_deg"], -350.0)

    def test_the_reported_joint_is_the_worst_one(self):
        raw = list(self.REFERENCE)
        raw[1] -= 40.0
        raw[4] += 120.0
        self.assertEqual(self.check(raw)["worst_joint"], 4)

    def test_refuses_angles_that_are_not_six_joints(self):
        with self.assertRaises(ValueError):
            self.check(self.REFERENCE[:5])


class ShortestTurnTests(unittest.TestCase):
    """The turnover the operator has to do, which is not the verdict.

    ``check_reference`` measures the literal difference because that is what the
    arm gets commanded; these are the same two angles measured as a physical
    move. Keeping them apart is deliberate -- see the docstrings -- so they get
    their own tests rather than being folded into the verdict's.
    """

    def test_a_short_move_the_other_way_is_short(self):
        # 322.8 and 14.2 are 51.4 apart going down through zero, and 308.6 the
        # other way. The verdict says 308.6; the turn has to say 51.4.
        self.assertAlmostEqual(shortest_turn(322.8, 14.2), -51.4, places=6)

    def test_it_is_the_short_way_round_the_rollover(self):
        # Ten degrees past the reference, but the reading rolled over: the
        # verdict is -350 (that is what the arm would be told) and the turn is
        # ten degrees (that is what the hand has to do).
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


if __name__ == "__main__":
    unittest.main()
