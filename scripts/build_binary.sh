#!/usr/bin/env bash
# Build the standalone E++ interpreter binary (dist/epp).
#
# Usage:
#   ./scripts/build_binary.sh            # build for the current OS
#
# The resulting binary is what the E++ IDE looks for automatically
# (dist/epp next to the repo root), and what `./dist/epp file.epp` runs.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Checking for PyInstaller..."
if ! python3 -m PyInstaller --version > /dev/null 2>&1; then
    echo "    Installing pyinstaller..."
    python3 -m pip install --user pyinstaller
fi

echo "==> Building dist/epp ..."
python3 -m PyInstaller --onefile --name epp run_epp.py --noconfirm \
    --hidden-import interpreter \
    --hidden-import interpreter.lexer \
    --hidden-import interpreter.parser \
    --hidden-import interpreter.evaluator \
    --hidden-import interpreter.stdlib \
    --hidden-import interpreter.errors \
    --hidden-import interpreter.nodes

echo "==> Done: $(ls -la dist/epp* 2>/dev/null || ls -la dist/)"
echo "    Try it: ./dist/epp hello.epp"
