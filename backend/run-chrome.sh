#!/bin/bash
# Start Xvfb if not running
if ! pgrep -f "Xvfb :99" > /dev/null 2>&1; then
    Xvfb :99 -screen 0 1280x720x24 -ac &>/dev/null &
    sleep 2
fi

export DISPLAY=:99

# Launch Chrome
/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome \
    --no-sandbox \
    --disable-dev-shm-usage \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    --no-first-run \
    --disable-gpu \
    --window-size=1280,720 \
    "https://notebooklm.google.com" &

CHROME_PID=$!
sleep 4

echo "Chrome PID: $CHROME_PID"
ss -tlnp | grep 9222
echo ""
echo "DevTools: http://localhost:9222"
