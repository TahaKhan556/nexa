"""NotebookLM Studio automation for audio/video/mindmap generation."""
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


# In-memory job queue (simple dict for now)
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


async def navigate_to_notebook(notebook_id: str) -> bool:
    """Navigate to a specific notebook."""
    notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"

    for attempt in range(5):
        url = await _cdp_eval("window.location.href")
        logger.info(f"Navigating: {url}")

        if notebook_id in url:
            return True

        await _cdp_eval(f"window.location.href = '{notebook_url}'")
        time.sleep(3)

    return False


async def click_studio_tab() -> bool:
    """Click the Studio tab in the NotebookLM interface."""
    result = await _cdp_eval("""
        (function() {
            // Look for Studio tab/button
            var elements = document.querySelectorAll('[role="tab"], button, a');
            for (var el of elements) {
                var text = el.textContent.toLowerCase();
                if (text.includes('studio')) {
                    el.click();
                    return 'clicked studio';
                }
            }
            // Try looking for the Studio section in the right panel
            var panels = document.querySelectorAll('[class*="studio"], [class*="Studio"]');
            if (panels.length > 0) {
                return 'studio panel found';
            }
            return 'no studio tab';
        })()
    """)
    logger.info(f"Studio tab: {result}")
    return result != 'no studio tab'


async def select_audio_format(format_type: str = "brief") -> bool:
    """Select audio format (brief, deep_dive, critique, debate)."""
    format_map = {
        "brief": "the brief",
        "deep_dive": "deep dive",
        "critique": "the critique",
        "debate": "the debate"
    }
    target_format = format_map.get(format_type, "the brief")

    result = await _cdp_eval(f"""
        (function() {{
            // Look for format selector
            var elements = document.querySelectorAll('button, [role="option"], [role="menuitem"]');
            for (var el of elements) {{
                var text = el.textContent.toLowerCase();
                if (text.includes('{target_format}')) {{
                    el.click();
                    return 'clicked ' + '{target_format}';
                }}
            }}
            return 'format not found';
        }})()
    """)
    logger.info(f"Audio format: {result}")
    return 'clicked' in result


async def click_generate_button() -> bool:
    """Click the Generate button to start audio/video generation."""
    result = await _cdp_eval("""
        (function() {
            // Look for Generate button
            var buttons = document.querySelectorAll('button');
            for (var btn of buttons) {
                var text = btn.textContent.toLowerCase();
                if (text.includes('generate') || text.includes('create')) {
                    btn.click();
                    return 'clicked generate';
                }
            }
            // Try aria-label
            var btn = document.querySelector('button[aria-label*="Generate"]');
            if (btn) {
                btn.click();
                return 'clicked aria generate';
            }
            return 'no generate button';
        })()
    """)
    logger.info(f"Generate button: {result}")
    return 'clicked' in result


async def wait_for_audio_player(timeout: int = 300) -> Optional[str]:
    """Wait for audio player to appear and extract the audio URL."""
    start = time.time()

    while time.time() - start < timeout:
        time.sleep(5)

        # Check for audio element
        audio_url = await _cdp_eval("""
            (function() {
                // Check for audio element
                var audio = document.querySelector('audio');
                if (audio) {
                    if (audio.src) return audio.src;
                    // Check source elements inside audio
                    var sources = audio.querySelectorAll('source');
                    for (var src of sources) {
                        if (src.src) return src.src;
                    }
                }
                
                // Check for any audio source elements anywhere
                var allSources = document.querySelectorAll('audio source, source[type*="audio"]');
                for (var src of allSources) {
                    if (src.src) return src.src;
                }
                
                // Check for download links with blob URLs
                var links = document.querySelectorAll('a[href*="blob:"], a[download], a[aria-label*="download"], a[aria-label*="Download"]');
                for (var link of links) {
                    if (link.href && (link.href.includes('blob:') || link.href.includes('audio'))) {
                        return link.href;
                    }
                }
                
                // Check for play buttons that might indicate audio is ready
                var playButtons = document.querySelectorAll('button[aria-label*="play"], button[aria-label*="Play"], [class*="play"]');
                if (playButtons.length > 0) {
                    // Look for nearby audio source
                    for (var btn of playButtons) {
                        var container = btn.closest('[class*="audio"], [class*="player"]');
                        if (container) {
                            var audioInContainer = container.querySelector('audio, source');
                            if (audioInContainer && audioInContainer.src) {
                                return audioInContainer.src;
                            }
                        }
                    }
                    // Return a marker that audio is ready
                    return 'audio_ready_marker';
                }
                
                return '';
            })()
        """)

        if audio_url:
            if audio_url == 'audio_ready_marker':
                logger.info("Audio player detected (play button found)")
                # Try to extract the actual URL from the player
                actual_url = await _cdp_eval("""
                    (function() {
                        var audio = document.querySelector('audio');
                        if (audio && audio.src) return audio.src;
                        var sources = document.querySelectorAll('source');
                        for (var src of sources) {
                            if (src.src) return src.src;
                        }
                        return '';
                    })()
                """)
                if actual_url:
                    return actual_url
                # If we can't get URL, return a success marker
                return 'audio_generated'
            
            logger.info(f"Audio URL found: {audio_url[:100]}...")
            return audio_url

        # Check if still generating
        status = await _cdp_eval("""
            (function() {
                var text = document.body.innerText;
                if (text.includes('Generating') || text.includes('Loading') || text.includes('Processing') || text.includes('Creating')) {
                    return 'generating';
                }
                // Check for audio player UI
                var audioElements = document.querySelectorAll('audio, [class*="audio-player"], [class*="player"]');
                if (audioElements.length > 0) {
                    return 'player_found';
                }
                return 'unknown';
            })()
        """)
        logger.info(f"Status: {status}")

    return None


async def wait_for_video_player(timeout: int = 1800) -> Optional[str]:
    """Wait for video player to appear and extract the video URL."""
    start = time.time()

    while time.time() - start < timeout:
        time.sleep(10)

        # Check for video element
        video_url = await _cdp_eval("""
            (function() {
                var video = document.querySelector('video');
                if (video && video.src) {
                    return video.src;
                }
                // Check for video source elements
                var sources = document.querySelectorAll('video source');
                for (var src of sources) {
                    if (src.src) return src.src;
                }
                // Check for download links
                var links = document.querySelectorAll('a[href*="video"], a[download]');
                for (var link of links) {
                    if (link.href && link.href.includes('blob:')) {
                        return link.href;
                    }
                }
                return '';
            })()
        """)

        if video_url:
            logger.info(f"Video URL found: {video_url[:100]}...")
            return video_url

        # Check if still generating
        status = await _cdp_eval("""
            (function() {
                var text = document.body.innerText;
                if (text.includes('Generating') || text.includes('Loading') || text.includes('Processing')) {
                    return 'generating';
                }
                return 'unknown';
            })()
        """)
        logger.info(f"Status: {status}")

    return None


async def click_mindmap_chip() -> bool:
    """Click the Mind Map suggestion chip in the chat area."""
    result = await _cdp_eval("""
        (function() {
            // Look for Mind Map chip
            var chips = document.querySelectorAll('[class*="chip"], [class*="suggestion"], button');
            for (var chip of chips) {
                var text = chip.textContent.toLowerCase();
                if (text.includes('mind map') || text.includes('mindmap')) {
                    chip.click();
                    return 'clicked mindmap chip';
                }
            }
            // Try typing "mind map" in the chat input
            var textarea = document.querySelector('textarea');
            if (textarea) {
                textarea.focus();
                textarea.value = 'Create a mind map';
                textarea.dispatchEvent(new Event('input', {bubbles: true}));
                return 'typed mindmap request';
            }
            return 'no mindmap chip';
        })()
    """)
    logger.info(f"Mind Map chip: {result}")
    
    # If we typed the request, submit it
    if 'typed' in result:
        await _cdp_eval("""
            (function() {
                var btn = document.querySelector('button[aria-label="Submit"]');
                if (btn) { btn.click(); return 'clicked'; }
                return 'no button';
            })()
        """)
        time.sleep(2)
    
    return 'clicked' in result or 'typed' in result


async def wait_for_mindmap(timeout: int = 120) -> Optional[str]:
    """Wait for mind map to appear and extract data."""
    start = time.time()

    while time.time() - start < timeout:
        time.sleep(3)

        # Try to extract SVG or canvas content
        mindmap_data = await _cdp_eval("""
            (function() {
                // Look for SVG elements (most common)
                var svgs = document.querySelectorAll('svg');
                for (var svg of svgs) {
                    // Skip small icons
                    if (svg.outerHTML.length > 500 && 
                        (svg.getAttribute('width') || svg.getAttribute('viewBox'))) {
                        return svg.outerHTML;
                    }
                }
                
                // Look for mind map container
                var containers = document.querySelectorAll('[class*="mindmap"], [class*="mind-map"], [class*="diagram"], [class*="graph"]');
                for (var container of containers) {
                    var innerSvg = container.querySelector('svg');
                    if (innerSvg && innerSvg.outerHTML.length > 500) {
                        return innerSvg.outerHTML;
                    }
                    // Check for canvas
                    var canvas = container.querySelector('canvas');
                    if (canvas) {
                        try {
                            return canvas.toDataURL('image/png');
                        } catch(e) {}
                    }
                }
                
                // Look for any large SVG (could be the mind map)
                var allSvgs = document.querySelectorAll('svg');
                var largestSvg = null;
                var maxSize = 0;
                for (var svg of allSvgs) {
                    var size = svg.outerHTML.length;
                    if (size > maxSize && size > 500) {
                        maxSize = size;
                        largestSvg = svg;
                    }
                }
                if (largestSvg) {
                    return largestSvg.outerHTML;
                }
                
                return '';
            })()
        """)

        if mindmap_data and len(mindmap_data) > 500:
            logger.info(f"Mind Map data found ({len(mindmap_data)} chars)")
            return mindmap_data
        
        # Check if generation is still in progress
        status = await _cdp_eval("""
            (function() {
                var text = document.body.innerText;
                if (text.includes('Generating') || text.includes('Loading') || text.includes('Creating')) {
                    return 'generating';
                }
                return 'unknown';
            })()
        """)
        logger.info(f"Mind Map status: {status}")

    return None


async def take_screenshot() -> str:
    """Take a screenshot of the current page."""
    import base64

    # Wait a bit for content to render
    time.sleep(2)
    
    # First, try to scroll to the mind map area
    await _cdp_eval("""
        (function() {
            // Look for mind map container and scroll to it
            var containers = document.querySelectorAll('[class*="mindmap"], [class*="mind-map"], [class*="diagram"]');
            if (containers.length > 0) {
                containers[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                return 'scrolled';
            }
            return 'no container';
        })()
    """)
    time.sleep(1)
    
    result = await _cdp_send("Page.captureScreenshot", {
        "format": "png",
        "captureBeyondViewport": True
    })
    
    if "result" in result and "data" in result["result"]:
        img_data = base64.b64decode(result["result"]["data"])
        filename = f"mindmap_{int(time.time())}.png"
        filepath = STUDIO_STORAGE / filename
        filepath.write_bytes(img_data)
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)

    return ""


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
