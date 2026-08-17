#!/usr/bin/env bash
# Deploy all project files to the Pico's filesystem.
# The Pico will run main.py automatically on every boot after deployment.
#
# Usage (from workspace root):
#   bash OpenCTDKd_multispectral/scripts/deploy.sh [PORT]
#
# PORT defaults to COM4; override with: bash scripts/deploy.sh COM5

set -e

PORT=${1:-COM4}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Deploying OpenCTDKd_multispectral to Pico on $PORT..."

mpremote connect "$PORT" fs mkdir :lib 2>/dev/null || true

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/ds3231.py" :lib/ds3231.py
echo "  copied lib/ds3231.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/rtc.py" :lib/rtc.py
echo "  copied lib/rtc.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/sdcard.py" :lib/sdcard.py
echo "  copied lib/sdcard.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/storage.py" :lib/storage.py
echo "  copied lib/storage.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/as7341.py" :lib/as7341.py
echo "  copied lib/as7341.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/spectral.py" :lib/spectral.py
echo "  copied lib/spectral.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/ms5837.py" :lib/ms5837.py
echo "  copied lib/ms5837.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/pressure.py" :lib/pressure.py
echo "  copied lib/pressure.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/tsys01.py" :lib/tsys01.py
echo "  copied lib/tsys01.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/temperature.py" :lib/temperature.py
echo "  copied lib/temperature.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/main.py" :main.py
echo "  copied main.py"

echo ""
echo "Deploy complete. Pico will now run main.py on every boot."
echo "To watch boot output: mpremote connect $PORT repl  (then Ctrl-D to soft reset)"
