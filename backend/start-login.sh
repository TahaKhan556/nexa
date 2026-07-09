#!/bin/bash
export DISPLAY=:99

# Start Xvfb if not running
if ! pgrep -f "Xvfb :99" > /dev/null 2>&1; then
    Xvfb :99 -screen 0 1280x720x24 -ac &
    sleep 2
fi

# Launch Chrome with remote debugging
/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome \
    --no-sandbox \
    --disable-dev-shm-usage \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --no-first-run \
    --disable-gpu \
    --window-size=1280,720 \
    "https://notebooklm.google.com" &
CHROME_PID=$!

sleep 3

echo ""
echo "Chrome running with PID: $CHROME_PID"
echo "Remote debugging: http://localhost:9222"
echo ""
echo "To connect from your Chrome:"
echo "  1. Go to chrome://inspect"
echo "  2. Click 'Configure...' next to Discover network targets"
echo "  3. Add: 23.94.206.104:9222"
echo "  4. Click Done"
echo "  5. Click 'inspect' on the NotebookLM page"
echo "  6. Log in with your Google account"
echo ""
echo "Waiting for login (5 minutes timeout)..."

# Wait for login (check every 5 seconds)
for i in $(seq 1 60); do
    sleep 5
    # Check if Chrome is still running
    if ! kill -0 $CHROME_PID 2>/dev/null; then
        echo "Chrome closed."
        break
    fi
done

echo "Done."
