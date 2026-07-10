"""NotebookLM chat automation using Chromium + CDP."""
import json
import logging
import subprocess
import time
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

CHROME_PROFILE = Path("/home/projects/nexa/data/chrome-profile")
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/32a12fd1-da7e-43d1-8ce8-aacb60460a00"
CDP_PORT = 9222


def _start_browser():
    """Start Chromium if not already running."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version").read()
        return
    except Exception:
        pass

    subprocess.run(["pkill", "-f", "chrome.*remote-debugging-port"], capture_output=True)
    subprocess.run(["pkill", "-f", "Xvfb :99"], capture_output=True)
    time.sleep(1)

    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x720x24", "-ac"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    import os
    os.environ["DISPLAY"] = ":99"

    subprocess.Popen([
        "/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
        "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-debugging-address=127.0.0.1",
        "--no-first-run",
        f"--user-data-dir={CHROME_PROFILE}",
        NOTEBOOK_URL,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)


async def _cdp_send(method: str, params: dict = None) -> dict:
    import websockets

    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    ws_url = None
    # Prefer notebook pages over homepage
    for t in targets:
        url = t.get("url", "")
        if t.get("type") == "page" and "/notebook/" in url and "notebooklm" in url.lower():
            ws_url = t.get("webSocketDebuggerUrl")
            break
    if not ws_url:
        # Fallback: any notebooklm page
        for t in targets:
            if "notebooklm" in t.get("url", "").lower():
                ws_url = t.get("webSocketDebuggerUrl")
                break
    if not ws_url:
        info = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version").read())
        ws_url = info.get("webSocketDebuggerUrl")
    if not ws_url:
        return {}

    async with websockets.connect(ws_url, close_timeout=5, ping_timeout=10) as ws:
        msg = {"id": 1, "method": method}
        if params:
            msg["params"] = params
        await ws.send(json.dumps(msg))
        return json.loads(await ws.recv())


async def _cdp_eval(expr: str) -> str:
    result = await _cdp_send("Runtime.evaluate", {"expression": expr})
    return result.get("result", {}).get("result", {}).get("value", "")


async def chat_with_notebooklm(prompt: str, notebook_id: str = None, timeout: int = 60) -> str:
    try:
        _start_browser()

        # Build notebook URL
        if notebook_id:
            notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"
        else:
            notebook_url = NOTEBOOK_URL

        # Navigate to notebook
        for attempt in range(5):
            url = await _cdp_eval("window.location.href")
            logger.info(f"URL: {url}")

            # Check if we're on the correct notebook
            if notebook_id and notebook_id in url:
                break
            elif "/notebook/" in url and not notebook_id:
                break

            # Use CDP Page.navigate (works with SPAs)
            await _cdp_send("Page.navigate", {"url": notebook_url})
            time.sleep(8)
        else:
            return "Not in a notebook."

        # Wait for textarea to appear
        textarea_found = False
        for attempt in range(10):
            type_result = await _cdp_eval("""
                (function() {
                    var ta = document.querySelector('textarea');
                    if (!ta) return 'no textarea';
                    return 'textarea found';
                })()
            """)
            if type_result == 'textarea found':
                textarea_found = True
                break
            time.sleep(1)

        if not textarea_found:
            return "Could not find chat input."

        # Type the prompt
        logger.info(f"Typing: {prompt[:50]}...")
        prompt_json = json.dumps(prompt)
        await _cdp_eval(f"""
            (function() {{
                var ta = document.querySelector('textarea');
                ta.focus();
                ta.value = {prompt_json};
                ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                return 'typed';
            }})()
        """)

        time.sleep(1)

        # Click send
        send_result = await _cdp_eval("""
            (function() {
                var btn = document.querySelector('button[aria-label="Submit"]');
                if (btn) { btn.click(); return 'clicked'; }
                return 'no send button';
            })()
        """)
        logger.info(f"Send result: {send_result}")

        if send_result == 'no send button':
            await _cdp_send("Input.dispatchKeyEvent", {
                "type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13
            })
            await _cdp_send("Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13
            })

        time.sleep(2)

        # Wait for response - simple approach: get the last response on the page
        logger.info("Waiting for response...")
        start = time.time()
        last_text = ""
        stable_count = 0

        while time.time() - start < timeout:
            time.sleep(2)
            text = await _cdp_eval("document.body.innerText")

            # Get the last 10000 chars (longer responses)
            recent = text[-10000:] if len(text) > 10000 else text
            lines = recent.split("\n")

            # Find the prompt in the page
            prompt_pos = -1
            for i, line in enumerate(lines):
                if prompt[:20] in line:
                    prompt_pos = i

            if prompt_pos < 0:
                continue

            # Get response after prompt
            response_lines = []
            for line in lines[prompt_pos + 1:]:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                # Skip UI elements
                if any(skip in line.lower() for skip in ["settings", "create notebook", "source", "menu", "search", "featured", "jump to bottom", "thumb", "copy", "rate", "scrolls", "arrow_forward", "thinking...", "loading...", "reply ready.", "since your notebook", "considering...", "exploring...", "analyzing...", "processing...", "generating...", "more_horiz", "save to note", "share", "export"]):
                    continue
                response_lines.append(line)

            if response_lines:
                candidate = "\n".join(response_lines)
                if len(candidate) > len(last_text):
                    last_text = candidate
                    stable_count = 0
                else:
                    stable_count += 1

                if stable_count >= 3 and len(last_text) > 30:
                    return last_text

        return last_text or "Could not capture response."

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return f"Error: {str(e)}"
