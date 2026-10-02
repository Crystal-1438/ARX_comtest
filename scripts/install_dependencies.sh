#!/usr/bin/env bash
# Install project dependencies. Does not configure CAN or construct a robot.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_MODE=sdk
PYTHON_COMMAND=python3
VENV_PATH="$PROJECT_ROOT/.venv"
SKIP_SYSTEM=0
DRY_RUN=0

usage() {
    cat <<'EOF'
Usage: bash scripts/install_dependencies.sh [options]
  --sdk             Install Python + native dependencies and build SDK (default)
  --mock            Install only Python runtime dependencies for simulation/tests
  --python PATH     Python 3.10+ interpreter (default: python3)
  --venv PATH       Environment location (default: project/.venv)
  --skip-system     Do not use apt/sudo; native dependencies must already exist
  --dry-run         Print commands without installing, building, or writing files
  -h, --help        Show this help

System packages use Debian/Ubuntu apt. SDK mode requires Linux x86_64 and
an available libkdl-parser-dev package (or --skip-system with existing KDL).
Run as your regular user; only apt commands use sudo. No motor commands are sent.
EOF
}

while (($#)); do
    case "$1" in
        --sdk) INSTALL_MODE=sdk; shift ;;
        --mock) INSTALL_MODE=mock; shift ;;
        --python|--venv)
            if (($# < 2)); then echo "Missing value for $1" >&2; exit 2; fi
            if [[ $1 == --python ]]; then PYTHON_COMMAND=$2; else VENV_PATH=$2; fi
            shift 2 ;;
        --skip-system) SKIP_SYSTEM=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

# Normalize a relative environment path before changing directories.
[[ $VENV_PATH = /* ]] || VENV_PATH="$PWD/$VENV_PATH"
run() {
    printf '+'; printf ' %q' "$@"; printf '\n'
    if (( ! DRY_RUN )); then "$@"; fi
}

if [[ $INSTALL_MODE == sdk ]] && [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo 'Bundled native SDK supports Linux x86_64 only; use --mock or obtain matching vendor libraries.' >&2
    exit 2
fi

if (( ! SKIP_SYSTEM )); then
    command -v apt-get >/dev/null || { echo 'apt-get unavailable; install dependencies manually and use --skip-system.' >&2; exit 2; }
    APT_PREFIX=()
    if (( EUID != 0 )); then APT_PREFIX=(sudo); fi
    PACKAGES=(python3-venv)
    if [[ $INSTALL_MODE == sdk ]]; then
        PACKAGES+=(python3-dev build-essential cmake pkg-config libkdl-parser-dev
                   liborocos-kdl-dev liburdfdom-dev can-utils iproute2)
    fi
    run "${APT_PREFIX[@]}" apt-get update
    if (( ! DRY_RUN )); then
        for package in "${PACKAGES[@]}"; do
            if ! LC_ALL=C apt-cache policy "$package" | awk '/Candidate:/ {if ($2 != "(none)") found=1} END {exit !found}'; then
                echo "No apt candidate for $package on this OS. No packages were installed." >&2
                echo 'Use a provisioned SDK environment with --skip-system, or a distribution that supplies these libraries.' >&2
                echo 'Ubuntu 22.04 universe supplies libkdl-parser-dev; do not mix distribution packages or rename incompatible libraries.' >&2
                exit 2
            fi
        done
    fi
    run "${APT_PREFIX[@]}" apt-get install -y --no-install-recommends "${PACKAGES[@]}"
fi

run "$PYTHON_COMMAND" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
if [[ ! -x "$VENV_PATH/bin/python" ]]; then
    run "$PYTHON_COMMAND" -m venv "$VENV_PATH"
else
    # Reuse only a matching interpreter; never silently rebuild an unrelated venv.
    if (( ! DRY_RUN )); then
        EXPECTED_VERSION=$("$PYTHON_COMMAND" -c 'import sys; print(sys.version_info[:2])')
        ACTUAL_VERSION=$("$VENV_PATH/bin/python" -c 'import sys; print(sys.version_info[:2])')
        if [[ $EXPECTED_VERSION != "$ACTUAL_VERSION" ]]; then
            echo 'Existing venv uses another Python version; pass its interpreter with --python or choose another --venv.' >&2
            exit 2
        fi
    fi
fi
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
[[ $INSTALL_MODE != sdk ]] || REQUIREMENTS="$PROJECT_ROOT/requirements-sdk.txt"
run "$VENV_PATH/bin/python" -m pip install -r "$REQUIREMENTS"
if [[ $INSTALL_MODE == sdk ]]; then
    run bash "$PROJECT_ROOT/scripts/build_sdk.sh" --python "$VENV_PATH/bin/python"
fi
if (( ! DRY_RUN )); then
    printf 'Installation completed (%s).\n' "$INSTALL_MODE"
    printf 'Run: ARX_VENV_DIR=%q bash %q --mode monitor --duration 1\n' "$VENV_PATH" "$PROJECT_ROOT/scripts/run.sh"
fi
