#!/usr/bin/env python3
"""
Login: Chrome + socat forwarding + CDP cookie capture.
User connects from their Chrome via public IP.
"""
import asyncio, json, os, subprocess, time, urllib.request
from pathlib import Path
from datetime import datetime, timedelta

DISPLAY = ":99"
PORT = 9222
PUBLIC_PORT = 9223
CHROME_PROFILE = Path("/home/projects/nexa/data/chrome-profile")
SESSION_FILE = Path("/home/projects/nexa/data/sessions/server_session.json")

# Start Xvfb
subprocess.run(["pkill", "-f", f"Xvfb {DISPLAY}"], capture_output=True)
time.sleep(1)
subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x720x24", "-ac"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
os.environ["DISPLAY"] = DISPLAY

# Kill old processes
subprocess.run(["pkill", "-9", "-f", "chrome.*remote-debugging"], capture_output=True)
subprocess.run(["fuser", "-k", f"{PUBLIC_PORT}/tcp"], capture_output=True)
time.sleep(1)

async def main():
    from playwright.async_api import async_playwright

    # Start socat to forward PUBLIC_PORT -> PORT
    socat = subprocess.Popen(
        ["socat", f"TCP-LISTEN:{PUBLIC_PORT},fork,reuseaddr,bind=0.0.0.0", f"TCP:127.0.0.1:{PORT}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    print(f"[1/3] socat forwarding {PUBLIC_PORT} -> {PORT}")

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_PROFILE),
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=[
                "--no-sandbox", "--disable-dev-shm-usage",
                f"--remote-debugging-port={PORT}",
                "--remote-debugging-address=127.0.0.1",
                "--no-first-run", "--disable-gpu",
            ],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=60000)

        try:
            ip = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=3).stdout.strip().split()[0]
        except:
            ip = "YOUR_SERVER_IP"

        print(f"\n[2/3] Chrome running")
        print()
        print("=" * 55)
        print("  ON YOUR COMPUTER (no SSH needed):")
        print()
        print("  1. Open Chrome → go to chrome://inspect")
        print("  2. Click 'Configure...' next to Discover")
        print(f"  3. Add: {ip}:{PUBLIC_PORT}")
        print("  4. Click Done")
        print("  5. Click 'inspect' on the NotebookLM page")
        print("  6. Log in with your Google account")
        print()
        print("  Press ENTER here when done")
        print("=" * 55)
        input()

        # Capture ALL cookies via CDP
        print("\n[3/3] Capturing cookies...")
        try:
            targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list").read())
            ws_url = None
            for t in targets:
                if "notebooklm" in t.get("url", "").lower() or "google" in t.get("url", "").lower():
                    ws_url = t.get("webSocketDebuggerUrl")
                    break
            if not ws_url:
                info = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version").read())
                ws_url = info.get("webSocketDebuggerUrl")

            import websockets
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
                result = json.loads(await ws.recv())
                all_cookies = result.get("result", {}).get("cookies", [])
        except Exception as e:
            print(f"  CDP error: {e}")
            all_cookies = []

        # Clean cookies
        clean = []
        for c in all_cookies:
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
            ss = c.get("sameSite", "")
            if ss in ("Strict", "Lax"):
                cookie["sameSite"] = ss
            clean.append(cookie)

        # Save session
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "storage_state": {"cookies": clean, "origins": []},
            "saved_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        SESSION_FILE.write_text(json.dumps(data, indent=2))

        # Report
        auth_names = ["SID", "HSID", "APISID", "SAPISID", "OSID", "__Secure-1PSID", "__Secure-3PSID"]
        found_auth = [c["name"] for c in clean if c["name"] in auth_names]
        print(f"\n  Total: {len(clean)} cookies")
        print(f"  Auth cookies: {found_auth}")
        print(f"  Saved to: {SESSION_FILE}")

        await context.close()
    socat.terminate()

asyncio.run(main())
