#!/usr/bin/env bash
#
# env_install.sh - prepare a Python + Jupyter environment on macOS, Linux or Windows (Git Bash).
#
# What it does:
#   1. pretty_print: readable messages (printf + blank lines, with colors)
#   2. detects the operating system with $OSTYPE
#   3. checks that Python 3 is installed, installs it if it is missing
#   4. checks that pip is available
#   5. installs Jupyter Notebook
#   6. on macOS, runs `brew doctor`
#
# Options:
#   --dry-run    print the commands instead of running them
#   --no-color   disable colors (useful when the output is redirected)
#   --help       show this help
#
# Every step is also written, with a timestamp, in env_install.log (next to the script).

set -euo pipefail   # strict mode: stop on errors, unset variables and failed pipes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/env_install.log"
DRY_RUN=0
USE_COLOR=1
OS=""
PY=""    # the command that runs Python 3 on this machine (python3, python or py)

# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------

color() {   # color <code> <text>
    if [ "$USE_COLOR" -eq 1 ]; then
        printf '\033[%sm%s\033[0m' "$1" "$2"
    else
        printf '%s' "$2"
    fi
}

log() {
    printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"
}

pretty_print() {   # pretty_print <message> [info|ok|warn|error]
    local level="${2:-info}" prefix
    case "$level" in
        ok)    prefix="$(color '1;32' '[ OK ]')" ;;
        warn)  prefix="$(color '1;33' '[WARN]')" ;;
        error) prefix="$(color '1;31' '[FAIL]')" ;;
        *)     prefix="$(color '1;34' '[INFO]')" ;;
    esac
    printf '\n%s %s\n\n' "$prefix" "$1"
    log "[$level] $1"
}

run() {   # run <command...> : execute, or only display it in dry-run mode
    log "run: $*"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '   (dry-run) %s\n' "$*"
        return 0
    fi
    "$@"
}

usage() {
    sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'
}

# ----------------------------------------------------------------------------
# Steps
# ----------------------------------------------------------------------------

detect_os() {
    case "$OSTYPE" in
        darwin*)        OS="macos" ;;
        linux*)         OS="linux" ;;
        msys*|cygwin*)  OS="windows" ;;   # Git Bash on Windows reports "msys"
        *)              OS="unknown" ;;
    esac
    pretty_print "Operating system: $OS (OSTYPE=$OSTYPE)"
    if [ "$OS" = "unknown" ]; then
        pretty_print "Unsupported system, install Python manually." error
        exit 1
    fi
}

find_python() {
    # On Windows the command is often "python" or "py", on Mac/Linux "python3".
    # "python3" can also be a fake Microsoft Store shortcut, so we run it to be sure.
    local candidate
    for candidate in python3 python py; do
        if "$candidate" --version 2>/dev/null | grep -q '^Python 3'; then
            PY="$candidate"
            return 0
        fi
    done
    return 1
}

install_python() {
    pretty_print "Python 3 not found, installing it..." warn
    case "$OS" in
        macos)
            command -v brew >/dev/null 2>&1 || { pretty_print "Homebrew is required: https://brew.sh" error; exit 1; }
            run brew install python ;;
        linux)
            run sudo apt-get update
            run sudo apt-get install -y python3 python3-pip ;;
        windows)
            run winget install -e --id Python.Python.3.12
            pretty_print "Close and reopen Git Bash so Windows finds the new python, then run the script again." warn
            exit 0 ;;
    esac
}

check_python() {
    if find_python; then
        pretty_print "Python found: $($PY --version 2>&1) (command: $PY)" ok
        return
    fi
    install_python
    if [ "$DRY_RUN" -eq 1 ]; then
        PY="python3"
        return
    fi
    find_python || { pretty_print "Python is still not available after the installation." error; exit 1; }
    pretty_print "Python installed: $($PY --version 2>&1)" ok
}

check_pip() {
    if "$PY" -m pip --version >/dev/null 2>&1; then
        pretty_print "pip found: $("$PY" -m pip --version | cut -d' ' -f1-2)" ok
        return
    fi
    pretty_print "pip not found, installing it..." warn
    if [ "$OS" = "linux" ]; then
        run sudo apt-get install -y python3-pip
    else
        run "$PY" -m ensurepip --upgrade
    fi
}

install_jupyter() {
    pretty_print "Installing Jupyter Notebook..."
    # Recent Homebrew and Debian/Ubuntu Pythons refuse "pip install" outside a virtual
    # environment (PEP 668). In that case we use the system package manager instead.
    if run "$PY" -m pip install --user notebook; then
        pretty_print "Jupyter Notebook installed. Start it with: $PY -m notebook" ok
        return
    fi
    pretty_print "pip refused to install globally, using the package manager instead." warn
    case "$OS" in
        macos) run brew install jupyterlab ;;
        linux) run sudo apt-get install -y jupyter-notebook ;;
        *)     pretty_print "Jupyter installation failed, see $LOG_FILE" error; exit 1 ;;
    esac
    pretty_print "Jupyter installed. Start it with: jupyter notebook" ok
}

check_brew() {
    [ "$OS" = "macos" ] || return 0
    pretty_print "Running brew doctor..."
    # brew doctor exits with an error code even for simple warnings: report, don't stop
    run brew doctor || pretty_print "brew doctor found some issues (see above)." warn
}

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

main() {
    local arg
    for arg in "$@"; do
        case "$arg" in
            --dry-run)  DRY_RUN=1 ;;
            --no-color) USE_COLOR=0 ;;
            -h|--help)  usage; exit 0 ;;
            *)          echo "Unknown option: $arg (see --help)"; exit 1 ;;
        esac
    done

    log "===== env_install.sh started (dry-run=$DRY_RUN) ====="
    pretty_print "Python environment setup"
    [ "$DRY_RUN" -eq 1 ] && pretty_print "Dry-run mode: nothing will be installed." warn

    detect_os
    check_python
    check_pip
    install_jupyter
    check_brew

    pretty_print "All done! Details in $LOG_FILE" ok
}

main "$@"
