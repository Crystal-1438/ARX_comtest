import json
import math
from pathlib import Path
import tempfile
import unittest

from leader_map import (JOINTS, JointMap, LeaderMap, Mapper, load_mapping,
                        resolve_mapping_path, uncalibrated)

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

    def test_missing_file_yields_uncalibrated_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            mapping = load_mapping(Path(directory) / "absent.json")
        self.assertFalse(mapping.calibrated)
        self.assertEqual(mapping.joints, uncalibrated().joints)
        self.assertTrue(all(joint.unwrap for joint in mapping.joints))


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
