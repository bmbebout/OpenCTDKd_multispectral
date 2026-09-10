#!/usr/bin/env bash
# Deploy all project files to the Pico's filesystem and reset.
# Kills any running mpremote first so COM4 is always free.
#
# Usage (from workspace root):
#   bash OpenCTDKd_multispectral/scripts/deploy.sh [PORT]
#
# PORT defaults to COM4; override with: bash scripts/deploy.sh COM5

set -e

PORT=${1:-COM4}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Kill any mpremote process holding the port before we start
python -c "import subprocess; subprocess.run(['taskkill', '/F', '/IM', 'mpremote.exe'], capture_output=True)" 2>/dev/null || true
sleep 1

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

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/neo6m.py" :lib/neo6m.py
echo "  copied lib/neo6m.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/gps.py" :lib/gps.py
echo "  copied lib/gps.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/oled.py" :lib/oled.py
echo "  copied lib/oled.py"

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

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/ezo_ec.py" :lib/ezo_ec.py
echo "  copied lib/ezo_ec.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/conductivity.py" :lib/conductivity.py
echo "  copied lib/conductivity.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/recording.py" :lib/recording.py
echo "  copied lib/recording.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/lib/webserver.py" :lib/webserver.py
echo "  copied lib/webserver.py"

mpremote connect "$PORT" fs cp "$PROJECT_DIR/main.py" :main.py
echo "  copied main.py"

echo ""
echo "Deploy complete."
echo "  To watch output: bash OpenCTDKd_multispectral/scripts/monitor.sh $PORT"

# Reset the Pico so it boots into the freshly deployed main.py
mpremote connect "$PORT" reset
