"""Offline checks against pinned binary constants, YAML and compiled C tables.

Never load the vendor library or construct a vendor controller.
"""
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / 'gravity_compensation/sdk_parameters'
DATA = json.loads((PARAMS / 'parameters.json').read_text())


def f32(value):
    return C.c_float(value).value


class SourceParametersTest(unittest.TestCase):
    def test_binary_constants_and_joint_mapping(self):
        binary = (ROOT / DATA['source']['binary']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), DATA['source']['sha256'])
        # Find file offsets via ELF64 program headers, not an assumed VA=offset.
        phoff = struct.unpack_from('<Q', binary, 32)[0]
        entsize, count = struct.unpack_from('<HH', binary, 54)
        for name, record in DATA['binary_constants'].items():
            address = int(record['virtual_address'], 16)
            for i in range(count):
                typ, _, offset, va, _, filesz, _, _ = struct.unpack_from(
                    '<IIQQQQQQ', binary, phoff + i * entsize)
                if typ == 1 and va <= address < va + filesz:
                    decoded = struct.unpack_from(
                        '<' + str(len(record['values'])) + record['format'],
                        binary, offset + address - va)
                    self.assertEqual(list(decoded), record['values'], name)
                    break
            else:
                self.fail('constant not in a file-backed ELF segment: ' + name)
        fields = {'position_min_rad': 'controller_lower_rad',
                  'position_max_rad': 'controller_upper_rad',
                  'position_kp': 'position_kp', 'position_kd': 'position_kd',
                  'position_ki': 'position_ki', 'protect_kd': 'protect_kd',
                  'feedback_current_threshold': 'feedback_current_threshold'}
        for i, joint in enumerate(DATA['joint_parameters']):
            for key, source in fields.items():
                self.assertEqual(joint[key], DATA['binary_constants'][source]['values'][i])
        for protocol in DATA['motor_protocols']:
            for key in ['position_min', 'position_max', 'velocity_min', 'velocity_max',
                        'effort_min', 'effort_max', 'kp_max', 'kd_max']:
                source = f"type{protocol['sdk_motor_type']}_{key}"
                self.assertEqual(protocol[key], DATA['binary_constants'][source]['values'][0])
        const = DATA['binary_constants']
        self.assertEqual(DATA['motor_type4_position']['feedback_recenter_span'],
                         const['type4_feedback_recenter_span']['values'][0])
        self.assertEqual(DATA['motor_type4_position']['command_wrap_span'],
                         2 * const['type4_command_half_wrap_span']['values'][0])
        self.assertEqual(DATA['motor_type4_position']['unwrap_span'],
                         2 * const['type4_position_max']['values'][0])
        control_sources = {
            'integral_limit': ('integral_limit_and_divisor', 0),
            'integral_divisor': ('integral_limit_and_divisor', 1),
            'home_acceleration': ('home_acceleration', 0),
            'home_speed': ('home_speed', 0),
            'home_position_tolerance': ('home_acceleration', 0),
            'home_velocity_tolerance': ('home_arrival_velocity', 0),
            'position_acceleration': ('position_interpolation', 0),
            'position_speed': ('position_interpolation', 1),
            'interpolation_actual_dt': ('interpolation_fixed_dt', 0)}
        for key, (source, index) in control_sources.items():
            self.assertEqual(DATA['controller_parameters'][key], const[source]['values'][index])

    def test_home_config_sources_and_urdf(self):
        profiles = ['ros1_remote_master', 'ros2_v2_collect']
        for source, profile in zip(DATA['source']['config_files'], profiles):
            raw = (PARAMS / source['copy']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            poses = re.findall(r'go_home_position:\s*\[([^\]]+)\]', raw.decode())
            self.assertEqual(len(poses), 2)
            for pose in poses:
                self.assertEqual([float(x) for x in pose.split(',')],
                                 DATA['home_profiles'][profile])
        for file in (PARAMS.parent / 'models').glob('*.urdf'):
            limits = ET.parse(file).findall('.//joint/limit')
            self.assertEqual(len(limits), 6)
            for limit in limits:
                self.assertEqual({k: float(v) for k, v in limit.attrib.items()},
                                 dict(lower=-10, upper=10, effort=100, velocity=1000))
        self.assertIsNone(DATA['gripper_motor']['home_rad'])
        self.assertFalse(DATA['gripper_motor']['current_threshold_checked'])


@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'requires host C compiler and nm')
class CParametersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        obj = Path(cls.temp.name) / 'parameters.o'
        so = Path(cls.temp.name) / 'parameters.so'
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-Wdouble-promotion', '-Wfloat-conversion', '-pedantic',
                        '-ffreestanding', '-fPIC', '-c',
                        str(PARAMS.parent / 'c/x5_sdk_parameters.c'), '-o', str(obj)], check=True)
        cls.undefined = subprocess.check_output(['nm', '-u', str(obj)], text=True).strip()
        subprocess.run(['cc', '-shared', str(obj), '-o', str(so)], check=True)
        cls.lib = C.CDLL(str(so))  # Only our readonly tables, never vendor code.

    def test_generated_c_and_no_dependencies(self):
        from gravity_compensation.sdk_parameters.generate_c import generate
        self.assertEqual((PARAMS.parent / 'c/x5_sdk_parameters.c').read_text(), generate(DATA))
        self.assertEqual(self.undefined, '')

    def test_compiled_joint_motor_and_protocol_tables(self):
        class Joint(C.Structure):
            _fields_ = [(k, C.c_float) for k in (
                'position_min_rad position_max_rad home_rad position_kp position_kd '
                'position_ki protect_kd sdk_gravity_scale').split()]

        class Motor(C.Structure):
            _fields_ = [(k, C.c_uint8) for k in
                        ['can_id', 'sdk_motor_type', 'protocol_index', 'current_check_active']]
            _fields_ += [('timeout_us', C.c_uint32), ('feedback_current_threshold', C.c_float)]

        class Protocol(C.Structure):
            _fields_ = [(k, C.c_float) for k in (
                'position_min position_max velocity_min velocity_max effort_min effort_max '
                'kp_min kp_max kd_min kd_max').split()]
            _fields_ += [('sdk_motor_type', C.c_uint8), ('quantization_bits', C.c_uint8 * 5),
                        ('packed_bits', C.c_uint8 * 5), ('command_dlc', C.c_uint8)]

        joints = (Joint * 6).in_dll(self.lib, 'x5_sdk_joints')
        for joint, expected in zip(joints, DATA['joint_parameters']):
            for key, _ in Joint._fields_:
                self.assertEqual(getattr(joint, key), f32(expected[key]))
        motors = (Motor * 7).in_dll(self.lib, 'x5_sdk_motors')
        self.assertEqual([m.can_id for m in motors], [1, 2, 4, 5, 6, 7, 8])
        self.assertEqual([m.sdk_motor_type for m in motors], [4, 4, 4, 2, 2, 2, 2])
        self.assertEqual([m.current_check_active for m in motors], [1] * 6 + [0])
        for m in motors:
            self.assertEqual(m.feedback_current_threshold, 13.0)
            self.assertEqual(m.timeout_us, 100000 if m.sdk_motor_type == 4 else 800000)
            self.assertEqual(m.protocol_index, int(m.sdk_motor_type == 4))
        protocols = (Protocol * 2).in_dll(self.lib, 'x5_sdk_protocols')
        for protocol, expected in zip(protocols, DATA['motor_protocols']):
            for key, _ in Protocol._fields_[:10]:
                self.assertEqual(getattr(protocol, key), f32(expected[key]))
            self.assertEqual(list(protocol.quantization_bits), expected['quantization_bits'])
            self.assertEqual(list(protocol.packed_bits), expected['packed_bits'])
            self.assertEqual(protocol.sdk_motor_type, expected['sdk_motor_type'])
            self.assertEqual(protocol.command_dlc, 8)
        homes = ((C.c_float * 6) * 3).in_dll(self.lib, 'x5_sdk_home_profiles')
        for home, key in zip(homes, ['sdk_default', 'ros1_remote_master', 'ros2_v2_collect']):
            self.assertEqual(list(home), list(map(f32, DATA['home_profiles'][key])))

    def test_compiled_control_gripper_and_auxiliary_tables(self):
        control_keys = ('integral_limit integral_divisor home_acceleration home_speed '
                        'home_position_tolerance home_velocity_tolerance position_acceleration '
                        'position_speed interpolation_argument3 interpolation_actual_dt '
                        'gripper_home_done_kd').split()
        counter_keys = ['overcurrent_samples', 'gripper_home_samples', 'write_motor_delay_us']

        class Control(C.Structure):
            _fields_ = [(k, C.c_float) for k in control_keys]
            _fields_ += [(k, C.c_uint16) for k in counter_keys]

        control = Control.in_dll(self.lib, 'x5_sdk_control')
        for key in control_keys:
            self.assertEqual(getattr(control, key), f32(DATA['controller_parameters'][key]))
        for key in counter_keys:
            self.assertEqual(getattr(control, key), DATA['controller_parameters'][key])
        gripper_keys = ('position_min_rad position_max_rad kp kd effort_min effort_max '
                        'error_gain position_bias home_velocity home_kd '
                        'contact_feedback_threshold contact_position_offset').split()

        class Gripper(C.Structure):
            _fields_ = [('position_limit_active', C.c_uint8), ('contact_check_active', C.c_uint8),
                        ('contact_samples', C.c_uint16)]
            _fields_ += [(k, C.c_float) for k in gripper_keys]

        grippers = (Gripper * 2).in_dll(self.lib, 'x5_sdk_gripper_profiles')
        for actual, expected in zip(grippers, DATA['gripper_profiles']):
            for key in gripper_keys:
                self.assertEqual(getattr(actual, key), f32(expected[key] or 0))
            for key in ['position_limit_active', 'contact_check_active', 'contact_samples']:
                self.assertEqual(getattr(actual, key), int(expected[key] or 0))
        for name, key in [('min', 'cartesian_lower'), ('max', 'cartesian_upper')]:
            actual = (C.c_float * 6).in_dll(self.lib, 'x5_sdk_cartesian_' + name)
            self.assertEqual(list(actual), list(map(f32, DATA['binary_constants'][key]['values'])))
        for symbol, section, keys in [
                ('x5_sdk_type4_position', 'motor_type4_position',
                 'offset feedback_min feedback_max unwrap_jump_threshold unwrap_span '
                 'command_wrap_span feedback_recenter_span'),
                ('x5_sdk_urdf_limits', 'urdf_limits',
                 'position_min_rad position_max_rad effort velocity')]:
            keys = keys.split()
            actual = (C.c_float * len(keys)).in_dll(self.lib, symbol)
            self.assertEqual(list(actual), [f32(DATA[section][k]) for k in keys])


if __name__ == '__main__':
    unittest.main()
