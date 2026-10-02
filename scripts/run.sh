#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_ROOT/scripts/env.sh"
if [[ ! -x $ARX_VENV_DIR/bin/python ]]; then
    echo 'Project Python environment missing; run scripts/install_dependencies.sh first.' >&2
    exit 2
fi
exec "$ARX_VENV_DIR/bin/python" "$PROJECT_ROOT/app.py" "$@"
