#!/usr/bin/env bash
# Run main.py directly from local source using mpremote mount.
# No file copying — the Pico reads all modules from the local filesystem.
# All serial print() output streams to this terminal.
#
# Usage (from workspace root):
#   bash OpenCTDKd_multispectral/scripts/dev_run.sh [PORT]

PORT=${1:-COM4}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Running main.py from local source on $PORT (Ctrl-C to stop)..."
echo ""

mpremote connect "$PORT" mount "$PROJECT_DIR" run "$PROJECT_DIR/main.py"
