#!/usr/bin/env bash
# Calibrate the leader against the arm's joint coordinates. The arm is never armed
# and never receives a target, but with --arm it is put in gravity compensation --
# motor-driven to hold its own weight -- and only handed back to SOFT after the
# tool asks. Keep it supported and stay with it; SOFT is zero torque, not disable.
#
#   bash scripts/calibrate.sh session --serial /dev/serial/by-id/usb-1a86_... \
#       --arm --model 2023
#   bash scripts/calibrate.sh fit calibration_session.jsonl --out leader_map.json
set -euo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_ROOT/scripts/env.sh"
if [[ ! -x $ARX_VENV_DIR/bin/python ]]; then
    echo 'Project Python environment missing; run scripts/install_dependencies.sh first.' >&2
    exit 2
fi
exec "$ARX_VENV_DIR/bin/python" "$PROJECT_ROOT/leader_calibrate.py" "$@"
