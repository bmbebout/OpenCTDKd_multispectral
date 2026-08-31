#!/usr/bin/env bash
# Kill any running mpremote, soft-reset the Pico, and tail its serial output.
# The Pico will run main.py from its own filesystem and stream print() output.
#
# Usage (from workspace root):
#   bash OpenCTDKd_multispectral/scripts/monitor.sh [PORT]

PORT=${1:-COM4}

# Kill any mpremote holding the port
python -c "import subprocess; subprocess.run(['taskkill', '/F', '/IM', 'mpremote.exe'], capture_output=True)" 2>/dev/null || true
sleep 1

echo "Resetting Pico on $PORT and tailing output (Ctrl-C to disconnect)..."
echo ""

# repl streams serial output; Ctrl-D in the REPL would soft-reset but here
# we just attach to watch whatever main.py prints without interrupting it.
mpremote connect "$PORT" repl
