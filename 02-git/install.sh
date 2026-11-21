#!/usr/bin/env bash
# install.sh - small setup script written on the feature branch (Git exercise, part 7).
# It checks the tools needed for the course and creates a Python virtual environment.

set -e

echo "== Checking the development tools =="

for tool in git python; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "[ok] $tool found: $("$tool" --version 2>&1)"
    else
        echo "[missing] $tool is not installed"
        exit 1
    fi
done

if [ ! -d ".venv" ]; then
    echo "== Creating a virtual environment in .venv =="
    python -m venv .venv
else
    echo "== .venv already exists, nothing to do =="
fi

echo "Done. Activate it with: source .venv/Scripts/activate (Windows) or source .venv/bin/activate (Mac/Linux)"
