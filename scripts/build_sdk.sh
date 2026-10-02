#!/usr/bin/env bash
# Rebuild Python bindings into .sdk without altering the pinned vendor snapshot.
set -euo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [[ ${1:-} == --python && $# == 2 ]]; then SDK_PYTHON=$2
elif (($#)); then echo 'Usage: bash scripts/build_sdk.sh [--python /path/to/python]' >&2; exit 2
fi
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo 'The pinned native libraries are Linux x86_64 only.' >&2; exit 2
fi
command -v cmake >/dev/null || { echo 'cmake missing; run install_dependencies.sh --sdk.' >&2; exit 2; }
"$SDK_PYTHON" -c 'import sys, sysconfig, pathlib; assert sys.version_info >= (3, 10); assert (pathlib.Path(sysconfig.get_path("include")) / "Python.h").is_file(), "Matching Python development headers missing"'
SDK_SOURCE="$PROJECT_ROOT/vendor/ARX_X5/py/arx_x5_python"
for library in "$SDK_SOURCE/bimanual/lib/arx_x5_src/libarx_x5_src.so" "$SDK_SOURCE/bimanual/lib/libx5_kinematic_solver.so"; do
    DEPENDENCIES=$(LC_ALL=C ldd "$library")
    if [[ $DEPENDENCIES == *'not found'* ]]; then
        printf 'Missing native dependencies for %s:\n%s\n' "$library" "$DEPENDENCIES" >&2
        echo 'Install KDL / kdl_parser or source the matching native-library environment before building.' >&2
        exit 2
    fi
done
PYBIND_DIRECTORY=$("$SDK_PYTHON" -m pybind11 --cmakedir)
PYTHON_TAG=$("$SDK_PYTHON" -c 'import sys; print(sys.implementation.cache_tag)')
BUILD_DIRECTORY="$PROJECT_ROOT/build/sdk-$PYTHON_TAG"
RUNTIME_DIRECTORY="$PROJECT_ROOT/.sdk"
mkdir -p "$RUNTIME_DIRECTORY"
# Invalidate the generated-runtime marker until both build and import checks succeed.
rm -f -- "$RUNTIME_DIRECTORY/READY"
cmake -S "$PROJECT_ROOT/scripts/native" -B "$BUILD_DIRECTORY" \
    -D"ARX_SDK_SOURCE=$SDK_SOURCE" -D"Python_EXECUTABLE=$SDK_PYTHON" \
    -D"pybind11_DIR=$PYBIND_DIRECTORY" -D"CMAKE_INSTALL_PREFIX=$RUNTIME_DIRECTORY" \
    -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIRECTORY" --parallel 2
cmake --install "$BUILD_DIRECTORY"
LD_LIBRARY_PATH="$RUNTIME_DIRECTORY/bimanual/api/arx_x5_src:$RUNTIME_DIRECTORY/bimanual/api${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    "$SDK_PYTHON" - "$PROJECT_ROOT" "$RUNTIME_DIRECTORY" <<'PY'
from pathlib import Path
import importlib
import sys
sys.path.insert(0, sys.argv[1])
from backends import load_sdk
sdk = load_sdk(sys.argv[2])
for method in ('set_arm_status', 'set_joint_positions', 'get_joint_positions', 'set_catch', 'arx_x'):
    assert hasattr(sdk.InterfacesPy, method), method
sys.path.insert(0, str(Path(sys.argv[2]) / 'bimanual/api/arx_x5_python'))
importlib.import_module('kinematic_solver')
print('SDK Python imports passed. No robot was constructed or commanded.')
PY
printf '%s\n' "$PYTHON_TAG" > "$RUNTIME_DIRECTORY/READY"
echo "SDK installed into $RUNTIME_DIRECTORY. Use scripts/run.sh or source scripts/env.sh."
