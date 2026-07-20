#!/usr/bin/env bash
# Run the deployed main.py from the Pico's filesystem and stream its output.
#
# Usage (from workspace root or project dir):
#   bash OpenCTDKd_multispectral/scripts/monitor.sh [PORT]

PORT=${1:-COM4}

echo "Running deployed main.py on $PORT..."
echo ""

mpremote connect "$PORT" exec "exec(open('main.py').read())"
