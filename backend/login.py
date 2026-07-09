"""
NotebookLM Login — Chrome Remote Debugging mode.

Works on headless servers. No VNC needed.

How it works:
  1. Starts a virtual display (Xvfb)
  2. Launches Chromium with remote debugging on port 9222
  3. You connect from YOUR Chrome browser to log in
  4. Script detects login and saves cookies automatically

Setup (one-time):
  On your LOCAL machine's Chrome browser:
    1. Open chrome://inspect
    2. Click "Configure..." (next to Discover network targets)
    3. Add: YOUR_SERVER_IP:9222
    4. Click Done
    5. You'll see "NotebookLM Login" under Remote Target
    6. Click "inspect" — a DevTools window opens showing the server's browser
    7. Log in with your Google account
    8. Script auto-detects login and saves cookies

Usage:
    python login.py
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

SESSION_DIR = Path(__file__).parent.parent / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SERVER_SESSION_FILE = SESSION_DIR / "server_session.json"

DISPLAY_NUM = 99
DEBUG_PORT = 9222


def kill_old_processes():
    """Kill any leftover login processes."""
    for pattern in ["Xvfb :99", "chrome.*playwright_chromiumdev_profile", "login.py"]:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern], capture_output=True, text=True, timeout=3
            )
            for pid in result.stdout.strip().split("\n"):
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except (ProcessLookupError, ValueError):
                        pass
        except Exception:
            pass


def start_xvfb():
    """Start Xvfb virtual framebuffer."""
    subprocess.Popen(
        ["Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1280x720x24", "-ac"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)


async def login():
    from playwright.async_api import async_playwright

    kill_old_processes()
    start_xvfb()
    os.environ["DISPLAY"] = f":{DISPLAY_NUM}"

    # Get server IP
    try:
        result = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, timeout=3
        )
        server_ip = result.stdout.strip().split()[0]
    except Exception:
        server_ip = "YOUR_SERVER_IP"

    print()
    print("=" * 60)
    print("  Nexa — NotebookLM Login (Chrome Remote Debugging)")
    print("=" * 60)
    print()
    print("  STEP 1: Open Chrome on YOUR computer")
    print(f"          Go to: chrome://inspect")
    print()
    print("  STEP 2: Click 'Configure...' next to")
    print("          'Discover network targets'")
    print()
    print(f"  STEP 3: Add this address:  {server_ip}:{DEBUG_PORT}")
    print("          Click Done")
    print()
    print("  STEP 4: You'll see 'NotebookLM Login' under Remote Target")
    print("          Click 'inspect' to open DevTools")
    print()
    print("  STEP 5: Log in with your Google account")
    print("          Script detects login automatically!")
    print()
    print("=" * 60)
    print()
    print("  Waiting for login... (up to 5 minutes)")
    print()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--remote-debugging-port={DEBUG_PORT}",
                "--remote-debugging-address=0.0.0.0",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=60000)

        try:
            await page.wait_for_url(
                lambda url: "notebooklm.google.com" in url and "accounts.google.com" not in url,
                timeout=300000,
            )
            await page.wait_for_timeout(3000)

            storage_state = await context.storage_state()
            session_data = {
                "storage_state": storage_state,
                "saved_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            }
            SERVER_SESSION_FILE.write_text(json.dumps(session_data, indent=2))

            print()
            print("=" * 60)
            print("  LOGIN SUCCESSFUL!")
            print(f"  Session saved to: {SERVER_SESSION_FILE}")
            print("  You can now use Nexa chat.")
            print("=" * 60)
            print()

        except Exception as e:
            print(f"\n  Login failed or timed out: {e}")
            print()

        await browser.close()


def main():
    asyncio.run(login())


if __name__ == "__main__":
    main()
