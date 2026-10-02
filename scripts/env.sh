#!/usr/bin/env bash
# Source this file; do not run it in a child shell.
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    echo 'Use: source scripts/env.sh' >&2
    exit 2
fi
_ARX_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export ARX_VENV_DIR="${ARX_VENV_DIR:-$_ARX_ROOT/.venv}"
if [[ -f $_ARX_ROOT/.sdk/READY ]]; then
    export ARX_SDK_ROOT="$_ARX_ROOT/.sdk"
else
    export ARX_SDK_ROOT="$_ARX_ROOT/vendor/ARX_X5/py/arx_x5_python"
fi
export LD_LIBRARY_PATH="$ARX_SDK_ROOT/bimanual/api/arx_x5_src:$ARX_SDK_ROOT/bimanual/api${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
unset _ARX_ROOT
