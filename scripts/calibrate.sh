#!/usr/bin/env bash
# Calibrate the leader against the arm's joint coordinates. Read-only: the arm is
# left in SOFT, is never armed and never receives a target.
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
