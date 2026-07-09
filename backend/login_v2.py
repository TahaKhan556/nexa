"""
Login to NotebookLM via Playwright with Xvfb + Chrome Remote Debugging.
Run: python login_v2.py

Then connect via Chrome DevTools from YOUR browser:
  1. Open chrome://inspect
  2. Add remote target: YOUR_SERVER_IP:9222
  3. Inspect the NotebookLM page and log in
  4. Press Enter in terminal when done
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

SESSION_DIR = Path(__file__).parent.parent / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SERVER_SESSION_FILE = SESSION_DIR / "server_session.json"

DISPLAY_NUM = ":99"
DEBUG_PORT = 9222


def start_xvfb():
    """Start Xvfb virtual display."""
    result = subprocess.run(["pgrep", "-f", f"Xvfb {DISPLAY_NUM}"], capture_output=True)
    if not result.stdout.strip():
        print(f"Starting Xvfb on {DISPLAY_NUM}...")
        subprocess.Popen(
            ["Xvfb", DISPLAY_NUM, "-screen", "0", "1280x720x24", "-ac"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(2)


async def login():
    from playwright.async_api import async_playwright

    start_xvfb()

    # Get server IP
    try:
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=3)
        server_ip = result.stdout.strip().split()[0]
    except Exception:
        server_ip = "YOUR_SERVER_IP"

    print()
    print("=" * 60)
    print("  Nexa NotebookLM Login")
    print("=" * 60)
    print()
    print("  ON YOUR COMPUTER:")
    print()
    print("  1. Open Chrome → go to chrome://inspect")
    print("  2. Click 'Configure...' next to Discover")
    print(f"  3. Add: {server_ip}:{DEBUG_PORT}")
    print("  4. Click Done")
    print("  5. Click 'inspect' on the NotebookLM page")
    print("  6. Log in with your Google account")
    print()
    print("  When login is complete, come back here and press ENTER")
    print("=" * 60)
    print()

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY_NUM

    async with async_playwright() as pw:
        # Launch Chrome with remote debugging
        browser = await pw.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--remote-debugging-port={DEBUG_PORT}",
                "--remote-debugging-address=0.0.0.0",
                "--no-first-run",
                "--disable-gpu",
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

        # Wait for user to press Enter
        input(">>> Press ENTER after you've logged in...")

        # Now capture ALL cookies from the browser
        # Navigate to google.com first to capture cross-domain cookies
        await page.goto("https://www.google.com", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Get storage state (captures ALL cookies)
        storage_state = await context.storage_state()

        # Also get cookies via CDP for more complete capture
        client = await context.new_cdp_session(page)
        result = await client.send("Network.getAllCookies")
        cdp_cookies = result.get("cookies", [])

        print(f"\nCaptured {len(storage_state['cookies'])} cookies via storage_state")
        print(f"Captured {len(cdp_cookies)} cookies via CDP")

        # Use CDP cookies (more complete)
        clean_cookies = []
        for c in cdp_cookies:
            cookie = {
                "name": c["name"],
                "value": c["value"],
                "domain": c["domain"],
                "path": c.get("path", "/"),
            }
            if c.get("expires") and c["expires"] > 0:
                cookie["expires"] = c["expires"]
            if c.get("httpOnly"):
                cookie["httpOnly"] = True
            if c.get("secure"):
                cookie["secure"] = True
            same_site = c.get("sameSite", "None")
            if same_site in ("Strict", "Lax"):
                cookie["sameSite"] = same_site
            clean_cookies.append(cookie)

        final_storage = {
            "cookies": clean_cookies,
            "origins": storage_state.get("origins", []),
        }

        session_data = {
            "storage_state": final_storage,
            "saved_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "method": "playwright_cdp",
        }
        SERVER_SESSION_FILE.write_text(json.dumps(session_data, indent=2))

        print(f"\nSession saved to: {SERVER_SESSION_FILE}")
        print(f"Total cookies saved: {len(clean_cookies)}")
        print("You can now use Nexa chat!\n")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(login())
