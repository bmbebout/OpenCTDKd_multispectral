#!/usr/bin/env bash
# Kill any running mpremote, then stream main.py output from the Pico.
# Safe to run at any time — interrupts whatever is currently running.
#
# Usage (from workspace root):
#   bash OpenCTDKd_multispectral/scripts/monitor.sh [PORT]

PORT=${1:-COM4}

# Kill any mpremote holding the port
python -c "import subprocess; subprocess.run(['taskkill', '/F', '/IM', 'mpremote.exe'], capture_output=True)" 2>/dev/null || true
sleep 1

echo "Connecting to Pico on $PORT and running main.py..."
echo ""

mpremote connect "$PORT" exec "exec(open('main.py').read())"
