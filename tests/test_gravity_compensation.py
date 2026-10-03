"""Offline physics/regression checks; no vendor imports or device access."""

import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from gravity_compensation import GravityCompensator, SDK_SCALES


class GravityTests(unittest.TestCase):
    def load_xml(self, xml, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "robot.urdf"
            path.write_text(xml)
            return GravityCompensator.from_urdf(path, **kwargs)

    def test_single_pendulum_analytic_sign_and_magnitude(self):
        model = self.load_xml('''<robot name="pendulum">
          <link name="base_link"/><link name="link6"><inertial>
            <mass value="2"/><origin xyz="0.5 0 0"/></inertial></link>
          <joint name="hinge" type="revolute"><parent link="base_link"/>
            <child link="link6"/><axis xyz="0 1 0"/></joint></robot>''')
        for q in (0, 0.2, -1.0, math.pi/2, math.pi):
            self.assertAlmostEqual(model.raw_torques([q])[0], -9.81*math.cos(q), places=12)

    def test_fixed_payload_and_prismatic_joint(self):
        model = self.load_xml('''<robot name="lift">
          <link name="base_link"/><link name="carriage"><inertial>
            <mass value="2"/></inertial></link>
          <link name="link6"><inertial><mass value="3"/>
            <origin xyz="1 0 0"/></inertial></link>
          <joint name="payload" type="fixed"><parent link="carriage"/>
            <child link="link6"/><origin xyz="0.5 0 0" rpy="0.2 0.3 0.4"/></joint>
          <joint name="lift" type="prismatic"><parent link="base_link"/>
            <child link="carriage"/><axis xyz="0 0 2"/></joint></robot>''')
        self.assertEqual(model.joint_names, ("lift",))
        self.assertAlmostEqual(model.raw_torques([0.7])[0], 5*9.81, places=12)
        with self.assertRaises(ValueError):
            model.sdk_torques([0.7])

    def test_potential_energy_gradient_all_models_and_tilted_gravity(self):
        rng = random.Random(513)
        step = 1e-6
        for name in ("2023", "master", "2025"):
            for gravity in ((0, 0, -9.81), (2.0, -3.0, -8.0)):
                model = GravityCompensator.from_model(name, gravity=gravity)
                for _ in range(12):
                    q = [rng.uniform(-2, 2) for _ in range(6)]
                    torque = model.raw_torques(q)
                    for i in range(6):
                        plus, minus = q.copy(), q.copy()
                        plus[i] += step
                        minus[i] -= step
                        derivative = (model.potential_energy(plus)-model.potential_energy(minus))/(2*step)
                        self.assertAlmostEqual(torque[i], derivative, delta=2e-8,
                                               msg=f"{name}, joint {i}, gravity={gravity}")

    def test_zero_gravity_and_gravity_reversal(self):
        q = (0.4, 0.7, -0.2, 1.2, -0.8, 0.1)
        zero = GravityCompensator.from_model("2025", gravity=(0, 0, 0))
        self.assertEqual(zero.raw_torques(q), (0.0,)*6)
        positive = GravityCompensator.from_model("2025", gravity=(0, 0, 9.81))
        negative = GravityCompensator.from_model("2025")
        for a, b in zip(positive.raw_torques(q), negative.raw_torques(q)):
            self.assertAlmostEqual(a, -b, places=12)

    def test_vendor_scaling_separate_from_physical_torque(self):
        model = GravityCompensator.from_model("2023")
        q = (0.4, -0.7, 0.2, 0.6, -0.3, 0.5)
        raw, sdk = model.raw_torques(q), model.sdk_torques(q)
        self.assertEqual(SDK_SCALES, (0.8, 0.8, 0.8, 1.32, 1.32, 1.32))
        for a, b, factor in zip(raw, sdk, SDK_SCALES):
            self.assertAlmostEqual(b, a*factor, places=12)

    def test_nonfinite_inputs_and_wrong_dof_rejected(self):
        model = GravityCompensator.from_model("2025")
        for q in ([0]*5, [0]*7, [math.nan]*6, [math.inf]*6):
            with self.assertRaises(ValueError):
                model.raw_torques(q)
        with self.assertRaises(ValueError):
            GravityCompensator.from_model("2025", gravity=(0, 0, math.nan))
        with self.assertRaises(ValueError):
            GravityCompensator.from_model("guess")

    def test_only_selected_chain_contributes(self):
        xml = '''<robot name="branch"><link name="base_link"><inertial>
          <mass value="999"/></inertial></link><link name="link6"><inertial>
          <mass value="1"/><origin xyz="1 0 0"/></inertial></link>
          <link name="sibling"><inertial><mass value="999"/></inertial></link>
          <joint name="hinge" type="revolute"><parent link="base_link"/>
          <child link="link6"/><axis xyz="0 1 0"/></joint>
          <joint name="branch" type="fixed"><parent link="base_link"/>
          <child link="sibling"/></joint></robot>'''
        self.assertAlmostEqual(self.load_xml(xml).raw_torques([0])[0], -9.81)

    def test_cli_needs_no_site_packages(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-S", "-m", "gravity_compensation",
                                 "--model", "2025", "--q", "0", "0", "0", "0", "0", "0"],
                                cwd=root, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["raw_torques_nm"]), 6)
        self.assertEqual(data["joint_names"], [f"joint{i}" for i in range(1, 7)])


if __name__ == "__main__":
    unittest.main()
