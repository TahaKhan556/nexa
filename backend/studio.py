"""NotebookLM Studio automation for audio/video/mindmap generation."""
import asyncio
import json
import logging
import subprocess
import time
import urllib.request
from pathlib import Path
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

CHROME_PROFILE = Path("/home/projects/nexa/data/chrome-profile")
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/32a12fd1-da7e-43d1-8ce8-aacb60460a00"
CDP_PORT = 9222
STUDIO_STORAGE = Path("/home/projects/nexa/storage/studio")
STUDIO_STORAGE.mkdir(parents=True, exist_ok=True)


class FeatureType(str, Enum):
    BRIEFING = "briefing"
    AUDIO = "audio"
    MINDMAP = "mindmap"
    VIDEO = "video"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


_jobs = {}


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
    """Send a CDP command to the browser."""
    import websockets

    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    ws_url = None
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
    """Evaluate JavaScript in the browser context."""
    result = await _cdp_send("Runtime.evaluate", {"expression": expr})
    return result.get("result", {}).get("result", {}).get("value", "")


async def _cdp_eval_async(expr: str) -> str:
    """Evaluate async JavaScript in the browser context (awaits Promises)."""
    import websockets

    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    ws_url = None
    for t in targets:
        if "notebooklm" in t.get("url", "").lower():
            ws_url = t.get("webSocketDebuggerUrl")
            break
    if not ws_url:
        info = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version").read())
        ws_url = info.get("webSocketDebuggerUrl")
    if not ws_url:
        return ""

    async with websockets.connect(ws_url, close_timeout=10, ping_timeout=60) as ws:
        msg = {"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expr,
            "awaitPromise": True,
        }}
        await ws.send(json.dumps(msg))
        return json.loads(await ws.recv()).get("result", {}).get("result", {}).get("value", "")


async def navigate_to_notebook(notebook_id: str) -> bool:
    """Navigate to a specific notebook."""
    notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"

    for attempt in range(5):
        url = await _cdp_eval("window.location.href")
        logger.info(f"Navigating: {url}")

        if notebook_id in url:
            time.sleep(3)
            return True

        await _cdp_eval(f"window.location.href = '{notebook_url}'")
        time.sleep(5)

    return False


async def check_notebook_has_sources() -> bool:
    """Check if the current notebook has any sources."""
    result = await _cdp_eval("""
        (function() {
            var text = document.body.innerText;
            if (text.includes("Saved sources will appear here")) return "no_sources";
            if (text.includes("Add source") || text.includes("Add sources")) return "has_add_button";
            return "unknown";
        })()
    """)
    logger.info(f"Source check: {result}")
    return result != "no_sources"


async def add_text_source(text: str) -> bool:
    """Add a text source to the notebook via Copied Text dialog."""
    # Click Sources tab first
    await _cdp_eval("""
        (function() {
            var tabs = document.querySelectorAll("[role='tab']");
            for (var tab of tabs) {
                if (tab.textContent.trim() === "Sources") {
                    tab.click();
                    return "clicked";
                }
            }
            return "not found";
        })()
    """)
    time.sleep(2)

    # Click "Add sources" button
    result = await _cdp_eval("""
        (function() {
            var buttons = document.querySelectorAll("button");
            for (var btn of buttons) {
                var text = btn.textContent.trim();
                if (text.includes("Add source")) {
                    btn.click();
                    return "clicked add source";
                }
            }
            return "not found";
        })()
    """)
    logger.info(f"Add source button: {result}")
    time.sleep(2)

    # Click "Copied text" option
    result = await _cdp_eval("""
        (function() {
            var buttons = document.querySelectorAll("button");
            for (var btn of buttons) {
                var text = btn.textContent.trim();
                if (text.includes("Copied text")) {
                    btn.click();
                    return "clicked copied text";
                }
            }
            return "not found";
        })()
    """)
    logger.info(f"Copied text button: {result}")
    time.sleep(2)

    # Paste text into the textarea
    escaped_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
    result = await _cdp_eval(f"""
        (function() {{
            var textareas = document.querySelectorAll("textarea");
            for (var ta of textareas) {{
                if (ta.placeholder === "Paste text here" && ta.offsetParent !== null) {{
                    ta.focus();
                    ta.value = '{escaped_text}';
                    ta.dispatchEvent(new Event("input", {{bubbles: true}}));
                    ta.dispatchEvent(new Event("change", {{bubbles: true}}));
                    return "text pasted, length=" + ta.value.length;
                }}
            }}
            return "textarea not found";
        }})()
    """)
    logger.info(f"Text paste: {result}")
    time.sleep(1)

    # Click "Insert" button
    result = await _cdp_eval("""
        (function() {
            var buttons = document.querySelectorAll("button");
            for (var btn of buttons) {
                if (btn.textContent.trim() === "Insert") {
                    btn.click();
                    return "clicked insert";
                }
            }
            return "not found";
        })()
    """)
    logger.info(f"Insert button: {result}")
    time.sleep(5)

    return "clicked" in result


async def click_studio_tab() -> bool:
    """Click the Studio tab in the NotebookLM interface."""
    result = await _cdp_eval("""
        (function() {
            var tabs = document.querySelectorAll("[role='tab']");
            for (var tab of tabs) {
                if (tab.textContent.trim() === "Studio") {
                    tab.click();
                    return "clicked Studio";
                }
            }
            return "not found";
        })()
    """)
    logger.info(f"Studio tab: {result}")
    return "clicked" in result


async def click_audio_overview() -> bool:
    """Click the Audio Overview button in the Studio panel."""
    result = await _cdp_eval("""
        (function() {
            var btn = document.querySelector("div[role='button'][aria-label='Audio Overview']");
            if (btn) {
                btn.click();
                return "clicked Audio Overview";
            }
            return "not found";
        })()
    """)
    logger.info(f"Audio Overview: {result}")
    return "clicked" in result


async def _fetch_blob_as_base64(blob_url: str) -> Optional[str]:
    """Fetch a blob URL in the browser and return base64-encoded data."""
    result = await _cdp_eval_async(f"""
        (async function() {{
            try {{
                var resp = await fetch('{blob_url}');
                var blob = await resp.blob();
                return await new Promise(function(resolve, reject) {{
                    var reader = new FileReader();
                    reader.onloadend = function() {{
                        // result is "data:audio/mpeg;base64,XXXX..."
                        var base64 = reader.result.split(',')[1];
                        resolve(base64);
                    }};
                    reader.onerror = reject;
                    reader.readAsDataURL(blob);
                }});
            }} catch(e) {{
                return '';
            }}
        }})()
    """)
    return result if result else None


async def _download_blob_via_cdp(job_id: str) -> Optional[str]:
    """Download audio from NotebookLM via CDP by intercepting the download click analytics."""
    import websockets
    import base64 as b64mod
    from urllib.parse import urlparse, parse_qs

    try:
        targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
        ws_url = None
        for t in targets:
            if "notebooklm" in t.get("url", "").lower() and t.get("type") == "page":
                ws_url = t.get("webSocketDebuggerUrl")
                break
        if not ws_url:
            return None

        msg_id = 1000

        async with websockets.connect(ws_url, close_timeout=5, ping_timeout=30) as ws:
            # 1. Set download behavior
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Browser.setDownloadBehavior", "params": {
                "behavior": "allow",
                "downloadPath": str(STUDIO_STORAGE),
                "eventsEnabled": True,
            }}))
            await ws.recv()

            # 2. Click Studio tab to make audio player visible
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                (function() {
                    var tabs = document.querySelectorAll('[role="tab"]');
                    for (var t of tabs) {
                        if (t.textContent.trim() === 'Studio') {
                            t.click();
                            return 'clicked Studio';
                        }
                    }
                    return 'Studio tab not found';
                })()
            """}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id:
                    break
            time.sleep(2)

            # 3. Inject fetch interceptor to capture analytics URLs
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                (function() {
                    window._audioUrls = [];
                    var origFetch = window.fetch;
                    window.fetch = function() {
                        var url = typeof arguments[0] === 'string' ? arguments[0] : (arguments[0].url || '');
                        window._audioUrls.push(url);
                        return origFetch.apply(this, arguments);
                    };
                    return 'ok';
                })()
            """}}))
            await ws.recv()

            # 4. Click play button to make audio player visible
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                (function() {
                    var plays = document.querySelectorAll("button[aria-label='Play']");
                    if (plays.length > 0) {
                        plays[0].click();
                        return 'clicked play';
                    }
                    return 'no play button';
                })()
            """}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id:
                    break
            time.sleep(3)

            # 5. Click "More options" on audio player
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                (function() {
                    var btns = document.querySelectorAll('button');
                    for (var b of btns) {
                        if (b.getAttribute('aria-label') === 'See more options for audio player') {
                            b.click();
                            return 'ok';
                        }
                    }
                    return 'not found';
                })()
            """}}))
            retry_count = 0
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id:
                    more_result = r.get("result", {}).get("result", {}).get("value", "")
                    if more_result == "not found" and retry_count < 5:
                        logger.info("Audio player not found, waiting...")
                        retry_count += 1
                        time.sleep(2)
                        msg_id += 1
                        await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                            (function() {
                                var btns = document.querySelectorAll('button');
                                for (var b of btns) {
                                    if (b.getAttribute('aria-label') === 'See more options for audio player') {
                                        b.click();
                                        return 'ok';
                                    }
                                }
                                return 'not found';
                            })()
                        """}}))
                        continue
                    break
            time.sleep(2)

            # 5. Click Download
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": """
                (function() {
                    var items = document.querySelectorAll('[role="menuitem"], mat-menu-item');
                    for (var m of items) {
                        if (m.textContent.trim().toLowerCase().includes('download')) {
                            m.click();
                            return 'ok';
                        }
                    }
                    return 'not found';
                })()
            """}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id:
                    break

            # 6. Wait for analytics request and extract audio URL
            time.sleep(3)
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify(window._audioUrls || [])"}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id:
                    all_urls = json.loads(r["result"]["result"]["value"])
                    break

            # Extract audio URL from analytics link_url parameter
            audio_url = None
            for url in all_urls:
                if "analytics" in url and "link_url" in url:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    link_url = params.get("ep.link_url", params.get("link_url", [""]))[0]
                    if link_url and ("googleapis.com" in link_url or "gstatic.com" in link_url or "googleusercontent.com" in link_url):
                        audio_url = link_url
                        break

            if not audio_url:
                logger.info("No audio URL found in analytics")
                return None

            logger.info(f"Found audio URL: {audio_url[:80]}...")

            # 7. Enable Network on main page to capture events
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Network.enable", "params": {}}))
            await ws.recv()

            # 8. Navigate main page to audio URL (triggers download via redirect)
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Page.navigate", "params": {"url": audio_url}}))

            # 9. Wait for download to complete
            download_guid = None
            start = time.time()
            while time.time() - start < 120:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2)
                    event = json.loads(raw)
                    method = event.get("method", "")

                    if method == "Browser.downloadWillBegin":
                        download_guid = event["params"].get("guid", "")
                        logger.info(f"Download started: {download_guid}")

                    elif method == "Browser.downloadProgress":
                        state = event["params"].get("state", "")
                        received = event["params"].get("receivedBytes", 0)
                        total = event["params"].get("totalBytes", 0)
                        if state == "completed":
                            filepath = event["params"].get("filePath", "")
                            logger.info(f"Download completed: {filepath} ({received} bytes)")
                            import shutil
                            ext = Path(filepath).suffix if Path(filepath).suffix else ".m4a"
                            new_path = STUDIO_STORAGE / f"{job_id}{ext}"
                            shutil.move(filepath, new_path)
                            logger.info(f"Renamed to: {new_path}")
                            return f"/api/studio/audio/{job_id}"
                        elif received > 0 and total > 0:
                            pct = int(received / total * 100)
                            logger.info(f"Download progress: {pct}% ({received}/{total})")

                except asyncio.TimeoutError:
                    continue

            # Navigate back to NotebookLM on timeout
            logger.warning("Download timed out, navigating back to NotebookLM")
            notebook_url = "https://notebooklm.google.com"
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Page.navigate", "params": {"url": notebook_url}}))

    except Exception as e:
        logger.error(f"CDP download failed: {e}")

    return None


async def wait_for_audio_player(timeout: int = 900, job_id: str = None) -> Optional[str]:
    """Wait for audio player to appear and extract/download the audio."""
    start = time.time()
    generating_seen = False

    while time.time() - start < timeout:
        time.sleep(10)

        # Check for audio element
        audio_url = await _cdp_eval("""
            (function() {
                // Check for audio element
                var audio = document.querySelector('audio');
                if (audio) {
                    if (audio.src) return audio.src;
                    var sources = audio.querySelectorAll('source');
                    for (var src of sources) {
                        if (src.src) return src.src;
                    }
                }
                
                // Check for download links
                var links = document.querySelectorAll('a[href*="blob:"], a[download], a[aria-label*="download"], a[aria-label*="Download"]');
                for (var link of links) {
                    if (link.href && (link.href.includes('blob:') || link.href.includes('audio'))) {
                        return link.href;
                    }
                }
                
                // Check for play buttons
                var playButtons = document.querySelectorAll('button[aria-label*="play"], button[aria-label*="Play"]');
                if (playButtons.length > 0) {
                    return 'audio_ready_marker';
                }
                
                return '';
            })()
        """)

        if audio_url:
            if audio_url == 'audio_ready_marker':
                logger.info("Audio player detected (play button found)")
                # Try to download the audio via CDP
                if job_id:
                    downloaded_url = await _download_blob_via_cdp(job_id)
                    if downloaded_url:
                        return downloaded_url
                return 'audio_generated'

            if audio_url.startswith('blob:'):
                logger.info(f"Blob URL detected: {audio_url[:80]}...")
                if job_id:
                    downloaded_url = await _download_blob_via_cdp(job_id)
                    if downloaded_url:
                        return downloaded_url
                return 'audio_generated'

            logger.info(f"Audio URL found: {audio_url[:100]}...")
            return audio_url

        # Check status
        status = await _cdp_eval("""
            (function() {
                var text = document.body.innerText;
                if (text.includes('Generating')) return 'generating';
                if (text.includes('Thinking')) return 'thinking';
                if (text.includes('Creating')) return 'creating';
                return 'unknown';
            })()
        """)
        elapsed = int(time.time() - start)
        logger.info(f"Status: {status} (elapsed: {elapsed}s)")

        if status == 'generating':
            generating_seen = True
        
        # If we were generating and now it's unknown, generation might be complete
        if generating_seen and status == 'unknown' and elapsed > 30:
            logger.info("Generation seems complete, checking for audio...")
            time.sleep(5)
            audio_url = await _cdp_eval("""
                (function() {
                    var audio = document.querySelector('audio');
                    if (audio && audio.src) return audio.src;
                    var playBtns = document.querySelectorAll('button[aria-label*="play"], button[aria-label*="Play"]');
                    if (playBtns.length > 0) return 'audio_ready_marker';
                    return '';
                })()
            """)
            if audio_url:
                if audio_url == 'audio_ready_marker':
                    if job_id:
                        downloaded_url = await _download_blob_via_cdp(job_id)
                        if downloaded_url:
                            return downloaded_url
                    return 'audio_generated'
                if audio_url.startswith('blob:') and job_id:
                    downloaded_url = await _download_blob_via_cdp(job_id)
                    if downloaded_url:
                        return downloaded_url
                return audio_url

    return None


def create_job(job_id: str, notebook_id: str, feature_type: FeatureType) -> dict:
    """Create a new generation job."""
    job = {
        "id": job_id,
        "notebook_id": notebook_id,
        "feature_type": feature_type.value,
        "status": GenerationStatus.PENDING.value,
        "content_url": None,
        "created_at": time.time(),
        "error": None
    }
    _jobs[job_id] = job
    return job


def update_job(job_id: str, **kwargs) -> dict:
    """Update a job's status."""
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)
    return _jobs.get(job_id, {})


def get_job(job_id: str) -> dict:
    """Get a job by ID."""
    return _jobs.get(job_id, {})
