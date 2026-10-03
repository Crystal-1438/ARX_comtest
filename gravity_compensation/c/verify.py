#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only float C validation against the independently verified Python model.

Python/compiler/ctypes are verification tools, never runtime dependencies of C.
"""
import argparse
import ctypes as C
import json
import math
import os
from pathlib import Path
import platform
import random
import shlex
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE.parent))
from gravity_compensation import GravityCompensator

Float6, Float3 = C.c_float * 6, C.c_float * 3
MODELS = ("2023", "master", "2025")


def compile_library(build, compiler, no_trig=False):
    stem = "x5_gravity_no_trig" if no_trig else "x5_gravity"
    flags = ["-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-Wdouble-promotion",
             "-Wfloat-conversion", "-pedantic", "-ffreestanding", "-fno-stack-protector", "-fPIC"]
    if no_trig:
        flags.append("-DX5_GRAVITY_NO_TRIG")
    obj = build / (stem + ".o")
    subprocess.run(compiler + flags + ["-c", str(SOURCE / "x5_gravity.c"), "-o", str(obj)], check=True)
    # A freestanding build must not import sin/cos, allocation, memcpy, or any
    # other runtime function. This check is on host GCC; an MCU without FPU may
    # require the compiler's own float arithmetic helpers instead.
    symbols = subprocess.check_output(["nm", "-u", str(obj)], text=True).strip()
    if symbols:
        raise AssertionError(f"unexpected runtime dependencies: {symbols}")
    library = build / (stem + ".so")
    subprocess.run(compiler + ["-shared", str(obj), "-o", str(library)], check=True)
    lib = C.CDLL(str(library))
    fptr = C.POINTER(C.c_float)
    lib.x5_gravity_compute_sincos.argtypes = [C.c_int, fptr, fptr, fptr, C.c_int, fptr]
    lib.x5_gravity_compute_sincos.restype = C.c_int
    if not no_trig:
        lib.x5_gravity_compute.argtypes = [C.c_int, fptr, fptr, C.c_int, fptr]
        lib.x5_gravity_compute.restype = C.c_int
    return lib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=PACKAGE.parent / "build/gravity-c")
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    compiler = shlex.split(args.cc)
    lib = compile_library(build, compiler)
    no_trig = compile_library(build, compiler, True)
    subprocess.run([sys.executable, str(SOURCE / "generate_model_data.py"), "--check"], check=True)
    rng = random.Random(20261003)
    poses = [[0.0]*6, [128.0]*6, [-128.0]*6, [math.pi/2]*6]
    # Include quadrant boundaries and float-rounded neighbors, not only random q.
    for k in range(-81, 82):
        for delta in (-1e-5, 0, 1e-5):
            poses.append([k*math.pi/2 + delta]*6)
    for _ in range(args.samples):
        poses.append([rng.uniform(-math.pi, math.pi) for _ in range(6)])
        poses.append([rng.uniform(-128, 128) for _ in range(6)])
    max_error, max_cached_error, count = 0.0, 0.0, 0
    for index, name in enumerate(MODELS):
        for gravity in (None, (2.0, -3.0, -8.0), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)):
            g = None if gravity is None else Float3(*gravity)
            reference = GravityCompensator.from_model(name, gravity=(0, 0, -9.81) if g is None else tuple(g))
            for pose in poses:
                q = Float6(*pose)  # Compare at the exact float inputs accepted by C.
                expected_raw = reference.raw_torques(tuple(q))
                sine, cosine = Float6(*(math.sin(x) for x in q)), Float6(*(math.cos(x) for x in q))
                for mode in (0, 1):
                    expected = expected_raw if mode == 0 else tuple(
                        t*(0.8 if j < 3 else 1.32) for j, t in enumerate(expected_raw))
                    out, cached, trimmed = Float6(), Float6(), Float6()
                    assert lib.x5_gravity_compute(index, q, g, mode, out) == 0
                    assert lib.x5_gravity_compute_sincos(index, sine, cosine, g, mode, cached) == 0
                    assert no_trig.x5_gravity_compute_sincos(index, sine, cosine, g, mode, trimmed) == 0
                    assert tuple(cached) == tuple(trimmed)
                    for a, b, c in zip(out, expected, cached):
                        if not math.isfinite(a) or not math.isfinite(c):
                            raise AssertionError("nonfinite C result")
                        error, cache_error = abs(a-b), abs(c-b)
                        if error > 1e-5 or cache_error > 1e-5:
                            raise AssertionError((name, tuple(q), gravity, mode, error, cache_error))
                        max_error, max_cached_error = max(max_error, error), max(max_cached_error, cache_error)
                    count += 1
    # Check API failures leave all outputs untouched, including NaN/Inf.
    for q in (None, Float6(math.nan, 0, 0, 0, 0, 0), Float6(math.inf, 0, 0, 0, 0, 0),
              Float6(128.01, 0, 0, 0, 0, 0)):
        out = Float6(*([123.0]*6))
        assert lib.x5_gravity_compute(0, q, None, 0, out) != 0
        assert tuple(out) == (123.0,)*6
    for model, mode, g in ((-1, 0, None), (3, 0, None), (0, 2, None),
                          (0, 0, Float3(math.nan, 0, -9.81))):
        out = Float6(*([123.0]*6))
        assert lib.x5_gravity_compute(model, Float6(), g, mode, out) != 0
        assert tuple(out) == (123.0,)*6
    assert lib.x5_gravity_compute(0, Float6(), None, 0, None) != 0
    assert lib.x5_gravity_compute_sincos(0, Float6(2, 0, 0, 0, 0, 0), Float6(), None, 0, Float6()) != 0
    fixtures = json.loads((PACKAGE / "verification/fixtures.json").read_text())
    fixture_error = 0.0
    for case in fixtures["cases"]:
        out = Float6()
        for mode, key in ((0, "raw"), (1, "sdk")):
            assert lib.x5_gravity_compute(MODELS.index(case["model"]), Float6(*case["q"]), None, mode, out) == 0
            fixture_error = max(fixture_error, *(abs(a-b) for a, b in zip(out, case[key])))
    assert fixture_error < 1e-5
    report = {"precision": "float only", "host": platform.machine(),
              "configurations_including_output_modes": count, "seed": 20261003,
              "maximum_angle_rad": 128, "max_absolute_error_nm": max_error,
              "precomputed_sincos_max_error_nm": max_cached_error,
              "kdl_vendor_fixture_max_error_nm": fixture_error,
              "core_undefined_symbols": [], "dynamic_allocation": False,
              "stm32_hardware_tested": False}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
