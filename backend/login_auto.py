#!/usr/bin/env python3
"""Automated NotebookLM login using Playwright — fills Google login form."""
import asyncio, os, subprocess, time
from pathlib import Path

DISPLAY = ":99"
CHROME_PROFILE = Path("/home/projects/nexa/data/chrome-profile")
EMAIL = "cooddder@gmail.com"
PASSWORD = "10times0<"

subprocess.run(["pkill", "-f", f"Xvfb {DISPLAY}"], capture_output=True)
time.sleep(1)
subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x720x24", "-ac"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
os.environ["DISPLAY"] = DISPLAY
CHROME_PROFILE.mkdir(parents=True, exist_ok=True)

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_PROFILE),
            headless=True,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("[1/4] Navigating to NotebookLM...")
        await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        print(f"  URL: {page.url}")

        # Check if already logged in
        if "accounts.google.com" not in page.url:
            print("  Already logged in!")
            await context.close()
            return

        print("[2/4] Filling email...")
        # Wait for the login form to load
        await page.wait_for_timeout(3000)

        # Try multiple selectors for email input
        email_selectors = [
            'input[type="email"]',
            'input[name="identifier"]',
            'input#identifierId',
            'input[aria-label="Email or phone"]',
        ]
        email_input = None
        for sel in email_selectors:
            try:
                el = page.locator(sel)
                if await el.count() > 0:
                    email_input = el.first
                    print(f"  Found email input: {sel}")
                    break
            except Exception:
                continue

        if not email_input:
            # Take screenshot for debugging
            await page.screenshot(path="/tmp/login_debug.png")
            print("  ERROR: Could not find email input. Screenshot saved to /tmp/login_debug.png")
            print(f"  Page URL: {page.url}")
            print(f"  Page title: {await page.title()}")
            await context.close()
            return

        await email_input.fill(EMAIL)
        await page.wait_for_timeout(1000)

        # Click Next
        next_btn = page.locator('#identifierNext button, button:has-text("Next")')
        await next_btn.first.click()
        await page.wait_for_timeout(3000)
        print(f"  URL after email: {page.url}")

        print("[3/4] Filling password...")
        await page.wait_for_timeout(3000)

        # Try multiple selectors for password input
        pw_selectors = [
            'input[type="password"]',
            'input[name="Passwd"]',
            'input[name="password"]',
            'input[aria-label="Enter your password"]',
        ]
        pw_input = None
        for sel in pw_selectors:
            try:
                el = page.locator(sel)
                if await el.count() > 0:
                    pw_input = el.first
                    print(f"  Found password input: {sel}")
                    break
            except Exception:
                continue

        if not pw_input:
            await page.screenshot(path="/tmp/login_debug_pw.png")
            print(f"  ERROR: Could not find password input. URL: {page.url}")
            await context.close()
            return

        await pw_input.fill(PASSWORD)
        await page.wait_for_timeout(1000)

        # Click Next
        next_btn = page.locator('#passwordNext button, button:has-text("Next")')
        await next_btn.first.click()
        await page.wait_for_timeout(5000)
        print(f"  URL after password: {page.url}")

        print("[4/4] Checking login status...")
        # Navigate to NotebookLM to verify
        await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        final_url = page.url
        print(f"  Final URL: {final_url}")

        if "accounts.google.com" not in final_url:
            print("\n  LOGIN SUCCESSFUL!")
            print(f"  Profile saved to: {CHROME_PROFILE}")
            print("  Nexa chat should work now!")
        else:
            print("\n  LOGIN FAILED — Google may have blocked automated login.")
            print("  Try running: python login_cdp.py (manual login via chrome://inspect)")

        await context.close()

asyncio.run(main())
