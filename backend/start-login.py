#!/usr/bin/env python3
"""Launch Chrome with remote debugging for NotebookLM login."""
import os
import subprocess
import sys
import time

DISPLAY = ":99"
CHROME = "/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
DEBUG_PORT = 9222

def main():
    # Start Xvfb if not running
    result = subprocess.run(["pgrep", "-f", "Xvfb :99"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("Starting Xvfb...")
        subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x720x24", "-ac"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY

    print(f"Starting Chrome on display {DISPLAY}...")
    proc = subprocess.Popen([
        CHROME,
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-debugging-address=127.0.0.1",
        "--no-first-run",
        "--disable-gpu",
        "--window-size=1280,720",
        "https://notebooklm.google.com",
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(5)

    # Verify Chrome is running
    result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    if f":{DEBUG_PORT}" in result.stdout:
        print(f"Chrome running (PID: {proc.pid})")
        print(f"Remote debugging: http://127.0.0.1:{DEBUG_PORT}")
        print()
        print("=" * 50)
        print("  NEXT STEPS:")
        print("=" * 50)
        print()
        print("  On YOUR computer, run in terminal:")
        print(f"    ssh -L {DEBUG_PORT}:localhost:{DEBUG_PORT} root@23.94.206.104")
        print()
        print("  Then in YOUR Chrome browser:")
        print("    1. Go to chrome://inspect")
        print("    2. Click 'Configure...' next to Discover")
        print(f"    3. Add: localhost:{DEBUG_PORT}")
        print("    4. Click 'inspect' on the NotebookLM page")
        print("    5. Log in with your Google account")
        print()
        print("  Script will detect login and save cookies.")
        print("=" * 50)
        print()
        print("  Waiting for login (5 min timeout)...")
        print()

        # Wait for login
        for i in range(60):
            time.sleep(5)
            if proc.poll() is not None:
                print("Chrome closed.")
                break
            # Check if session was saved
            session_file = "/home/projects/nexa/data/sessions/server_session.json"
            if os.path.exists(session_file):
                mtime = os.path.getmtime(session_file)
                if mtime > time.time() - 10:
                    print("LOGIN DETECTED! Session saved.")
                    break
    else:
        print("ERROR: Chrome failed to start.")
        proc.kill()
        sys.exit(1)

    proc.terminate()
    print("Done.")

if __name__ == "__main__":
    main()
