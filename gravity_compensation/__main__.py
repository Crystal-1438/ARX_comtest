# SPDX-License-Identifier: LGPL-2.1-or-later
"""Offline CLI: python3 -m gravity_compensation --model 2025 --q 0 0 0 0 0 0"""

import argparse
import json

from .solver import GravityCompensator, MODEL_FILES, SDK_SCALES


def main():
    parser = argparse.ArgumentParser(description="Offline ARX X5 gravity calculation (no CAN/SDK)")
    parser.add_argument("--model", required=True, choices=MODEL_FILES)
    parser.add_argument("--q", nargs=6, type=float, required=True, metavar="RAD")
    parser.add_argument("--gravity", nargs=3, type=float, default=(0, 0, -9.81), metavar="M_S2")
    args = parser.parse_args()
    try:
        solver = GravityCompensator.from_model(args.model, gravity=args.gravity)
        raw = solver.raw_torques(args.q)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({"model": args.model, "joint_names": solver.joint_names,
                      "q_rad": args.q, "gravity_m_s2": solver.gravity,
                      "raw_torques_nm": raw, "sdk_scales": SDK_SCALES,
                      "sdk_torques_nm": solver.sdk_torques(args.q)}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
