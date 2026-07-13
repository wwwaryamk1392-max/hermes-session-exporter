#!/usr/bin/env bash
# hermes-session-exporter installer
# Usage: curl -fsSL https://raw.githubusercontent.com/wwwaryamk1392-max/hermes-session-exporter/main/install.sh | bash

set -euo pipefail

REPO="wwwaryamk1392-max/hermes-session-exporter"
INSTALL_DIR="${HOME}/.local/bin"

echo "Installing hermes-session-exporter..."

# Check Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "Error: Python 3.10+ required"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python $PY_VERSION"

# Install via pipx if available, else pip
if command -v pipx &>/dev/null; then
    echo "Installing via pipx..."
    pipx install git+https://github.com/$REPO.git
elif command -v pip &>/dev/null; then
    echo "Installing via pip (--user)..."
    pip install --user git+https://github.com/$REPO.git
    echo "Ensure $INSTALL_DIR is in PATH"
else
    echo "Error: pip or pipx required"
    exit 1
fi

echo "Done! Run: hermes-session-exporter"