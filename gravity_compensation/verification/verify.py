#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Compare the standalone implementation against real KDL and optional ARX math.

Uses an independently serialized URDF chain, not the implementation's loader.
The optional vendor probe is deliberately hash/architecture locked and does not
construct any vendor object, initialize CAN, or run a controller thread.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE.parent))
from gravity_compensation import GravityCompensator  # noqa: E402

VENDOR_SHA256 = "cb51e1acfccd1e904ca263d45db2035fb33a457ded0b64e5376a864aaf1abeb5"
MODELS = {"2023": "x5.urdf", "master": "x5_master.urdf", "2025": "x5_2025.urdf"}


def serialize_model(path):
    """Raw XML numbers -> C++ KDL construction, independent of urdf.py."""
    root = ET.parse(path).getroot()
    links = {link.attrib["name"]: link for link in root.findall("link")}
    joints = {j.find("child").attrib["link"]: j for j in root.findall("joint")}
    chain, child = [], "link6"
    while child != "base_link":
        joint = joints[child]
        chain.append((joint, links[child]))
        child = joint.find("parent").attrib["link"]
    lines = [str(len(chain))]
    for joint, link in reversed(chain):
        origin, axis, inertial = joint.find("origin"), joint.find("axis"), link.find("inertial")
        xyz = "0 0 0" if origin is None else origin.get("xyz", "0 0 0")
        rpy = "0 0 0" if origin is None else origin.get("rpy", "0 0 0")
        axis = "1 0 0" if axis is None else axis.get("xyz", "1 0 0")
        mass, com = "0", "0 0 0"
        if inertial is not None:
            mass = inertial.find("mass").attrib["value"]
            if inertial.find("origin") is not None:
                com = inertial.find("origin").get("xyz", "0 0 0")
        kind = {"fixed": 0, "revolute": 1, "continuous": 1, "prismatic": 2}[joint.attrib["type"]]
        lines.append(f"{kind} {xyz} {rpy} {axis} {mass} {com}")
    return "\n".join(lines) + "\n"


def query(executable, description, gravity, poses, vendor=None):
    data = description + " ".join(map(str, gravity)) + "\n" + str(len(poses)) + "\n"
    data += "\n".join(" ".join(map(str, q)) for q in poses) + "\n"
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(executable.parent) + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    command = [str(executable)] + ([str(vendor)] if vendor else [])
    result = subprocess.run(command, input=data, text=True, capture_output=True,
                            check=True, env=env, timeout=30)
    values = [tuple(map(float, row.split())) for row in result.stdout.splitlines()]
    if len(values) != len(poses) or any(len(row) != 6 for row in values):
        raise RuntimeError(f"unexpected native result: {result.stdout[:300]}")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=PACKAGE.parent / "build/gravity-reference")
    parser.add_argument("--vendor-library", type=Path,
                        help="optional pinned x86_64 libarx_x5_src.so (math-only ABI probe)")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--fixtures", type=Path, help="write independently computed regression cases")
    args = parser.parse_args()
    executable = args.build_dir.resolve() / "kdl_reference"
    if args.fixtures and not args.vendor_library:
        parser.error("--fixtures requires --vendor-library to preserve both independent references")
    if args.vendor_library:
        args.vendor_library = args.vendor_library.resolve()
        if platform.machine() != "x86_64" or hashlib.sha256(args.vendor_library.read_bytes()).hexdigest() != VENDOR_SHA256:
            parser.error("vendor probe only supports the documented x86_64 binary SHA256")
    rng = random.Random(20261003)
    poses = [[0.0]*6, [0.0, 0.2, -0.3, 0.1, 0.0, 0.0],
             [0.3, -0.7, 0.4, 0.5, -0.2, 0.8], [math.pi/2]*6, [-math.pi/2]*6]
    poses += [[rng.uniform(-math.pi, math.pi) for _ in range(6)] for _ in range(100)]
    report = {"kdl_version": "1.5.1", "seed": 20261003, "poses_per_model": len(poses),
              "vendor_library_sha256": VENDOR_SHA256 if args.vendor_library else None,
              "raw_max_abs_error": 0.0, "vendor_max_abs_error": None,
              "raw_configurations": 0, "vendor_configurations": 0,
              "scope": "offline math only; no vendor constructors/CAN/hardware"}
    fixtures = {"source": "real KDL 1.5.1 JntToGravity", "cases": []}
    for name, filename in MODELS.items():
        description = serialize_model(PACKAGE / "models" / filename)
        for gravity in ((0.0, 0.0, -9.81), (2.0, -3.0, -8.0), (0.0, 0.0, 0.0)):
            oracle = query(executable, description, gravity, poses)
            model = GravityCompensator.from_model(name, gravity=gravity)
            for q, expected in zip(poses, oracle):
                error = max(abs(a-b) for a, b in zip(model.raw_torques(q), expected))
                if not math.isfinite(error) or error > 1e-10:
                    raise AssertionError((name, gravity, q, error))
                report["raw_max_abs_error"] = max(report["raw_max_abs_error"], error)
            report["raw_configurations"] += len(poses)
            if gravity == (0.0, 0.0, -9.81):
                vendor_values = query(executable, description, gravity, poses, args.vendor_library) if args.vendor_library else None
                if vendor_values is not None:
                    for q, expected in zip(poses, vendor_values):
                        error = max(abs(a-b) for a, b in zip(model.sdk_torques(q), expected))
                        if not math.isfinite(error) or error > 1e-10:
                            raise AssertionError(("vendor", name, q, error))
                        report["vendor_max_abs_error"] = max(report["vendor_max_abs_error"] or 0.0, error)
                    report["vendor_configurations"] += len(poses)
                for i in range(5):
                    case = {"model": name, "q": poses[i], "raw": oracle[i]}
                    if vendor_values is not None:
                        case["sdk"] = vendor_values[i]
                    fixtures["cases"].append(case)
    if args.vendor_library:
        fixtures["vendor_source"] = {"sha256": VENDOR_SHA256, "method": "computeGravityCompensationTorque; ABI probe"}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    if args.fixtures:
        args.fixtures.write_text(json.dumps(fixtures, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
