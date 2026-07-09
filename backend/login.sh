#!/bin/bash
# Login: Chromium + remote debugging + socat forwarding
# User connects via chrome://inspect and logs in manually

set -e

PROFILE="/home/projects/nexa/data/chrome-profile"
PORT=9222
PUBLIC_PORT=9223

# Cleanup
pkill -f "Xvfb :99" 2>/dev/null || true
fuser -k $PORT/tcp 2>/dev/null || true
fuser -k $PUBLIC_PORT/tcp 2>/dev/null || true
sleep 1

# Start Xvfb
Xvfb :99 -screen 0 1280x720x24 -ac &>/dev/null &
sleep 2
export DISPLAY=:99

# Start socat
socat TCP-LISTEN:$PUBLIC_PORT,fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:$PORT &>/dev/null &
sleep 1

# Start Chromium with remote debugging and persistent profile
mkdir -p "$PROFILE"
/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome \
    --no-sandbox \
    --disable-dev-shm-usage \
    --remote-debugging-port=$PORT \
    --remote-debugging-address=127.0.0.1 \
    --no-first-run \
    --disable-gpu \
    --user-data-dir="$PROFILE" \
    "https://notebooklm.google.com" &>/dev/null &
CHROME_PID=$!

sleep 4

# Get server IP
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  Login to NotebookLM"
echo "=========================================="
echo ""
echo "  ON YOUR COMPUTER:"
echo ""
echo "  1. Open Chrome → chrome://inspect"
echo "  2. Configure → Add: ${IP}:${PUBLIC_PORT}"
echo "  3. Inspect the NotebookLM page"
echo "  4. Log in with your Google account"
echo ""
echo "  Press ENTER here when done"
echo "=========================================="
echo ""

read -p ">>> Press ENTER when login is complete: "

# Check cookies
echo ""
echo "Checking session..."
COOKIES=$(python3 -c "
import sqlite3, os
db = '$PROFILE/Default/Cookies'
if os.path.exists(db):
    conn = sqlite3.connect(db)
    rows = conn.execute('SELECT name FROM cookies WHERE host_key LIKE \"%google%\"').fetchall()
    print(f'{len(rows)} Google cookies found')
    names = [r[0] for r in rows]
    auth = ['SID','HSID','APISID','SAPISID','OSID']
    found = [n for n in names if n in auth]
    print(f'Auth cookies: {found}')
    conn.close()
else:
    print('No cookie database found')
" 2>/dev/null)

echo "$COOKIES"

# Cleanup
kill $CHROME_PID 2>/dev/null
fuser -k $PORT/tcp 2>/dev/null
fuser -k $PUBLIC_PORT/tcp 2>/dev/null
pkill -f "Xvfb :99" 2>/dev/null

echo ""
echo "Session saved to: $PROFILE"
echo "You can now use Nexa chat!"
