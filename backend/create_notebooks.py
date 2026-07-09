"""Create 5 notebooks in NotebookLM with URL sources."""
import json
import urllib.request
import asyncio
import websockets
import time

CDP_PORT = 9222

# 5 Universal topic notebooks with sources
NOTEBOOKS = [
    {
        "name": "Science & Technology",
        "description": "Physics, chemistry, biology, computer science, AI, engineering",
        "sources": [
            "https://en.wikipedia.org/wiki/Science",
            "https://en.wikipedia.org/wiki/Technology",
            "https://en.wikipedia.org/wiki/Artificial_intelligence",
        ]
    },
    {
        "name": "History & World Events",
        "description": "World history, civilizations, wars, political events, geography",
        "sources": [
            "https://en.wikipedia.org/wiki/World_history",
            "https://en.wikipedia.org/wiki/List_of_historical_events",
            "https://en.wikipedia.org/wiki/History_of_the_World",
        ]
    },
    {
        "name": "Mathematics & Logic",
        "description": "Algebra, calculus, statistics, logic, problem solving",
        "sources": [
            "https://en.wikipedia.org/wiki/Mathematics",
            "https://en.wikipedia.org/wiki/Statistics",
            "https://en.wikipedia.org/wiki/Logic",
        ]
    },
    {
        "name": "Language & Literature",
        "description": "Writing, grammar, literature analysis, communication, languages",
        "sources": [
            "https://en.wikipedia.org/wiki/Language",
            "https://en.wikipedia.org/wiki/Literature",
            "https://en.wikipedia.org/wiki/Grammar",
        ]
    },
    {
        "name": "Business & Economics",
        "description": "Finance, marketing, management, economics, entrepreneurship",
        "sources": [
            "https://en.wikipedia.org/wiki/Business",
            "https://en.wikipedia.org/wiki/Economics",
            "https://en.wikipedia.org/wiki/Finance",
        ]
    }
]

async def cdp_send(ws, method, params=None):
    msg = {"id": 1, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    return json.loads(await ws.recv())

async def cdp_eval(ws, expr):
    result = await cdp_send(ws, "Runtime.evaluate", {"expression": expr})
    return result.get("result", {}).get("result", {}).get("value", "")

async def create_notebook(ws, notebook_info):
    """Create a new notebook and return its ID."""
    print(f"\nCreating notebook: {notebook_info['name']}")

    # Click "Create new notebook" button
    await cdp_eval(ws, """
        (function() {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                var aria = btn.getAttribute('aria-label') || '';
                if (aria.includes('Create new notebook') || aria.includes('Create new')) {
                    btn.click();
                    return 'clicked';
                }
            }
            return 'not found';
        })()
    """)
    time.sleep(5)

    # Get the new notebook URL
    url = await cdp_eval(ws, "window.location.href")
    print(f"  New URL: {url}")

    # Extract notebook ID from URL
    if "/notebook/" in url:
        notebook_id = url.split("/notebook/")[-1].split("?")[0]
        print(f"  Notebook ID: {notebook_id}")
        return notebook_id
    else:
        print("  Failed to create notebook")
        return None

async def add_source(ws, notebook_id, url):
    """Add a URL source to a notebook."""
    print(f"  Adding source: {url}")

    # Click "Add source" or "Sources" tab
    await cdp_eval(ws, """
        (function() {
            // Click on Sources tab or Add source button
            var elements = document.querySelectorAll('button, a, [role="tab"]');
            for (var el of elements) {
                var text = el.textContent.toLowerCase();
                if (text.includes('source') || text.includes('add')) {
                    el.click();
                    return 'clicked source';
                }
            }
            return 'no source button';
        })()
    """)
    time.sleep(2)

    # Look for URL input or "Website" option
    await cdp_eval(ws, """
        (function() {
            // Try to find and click "Website" or "URL" option
            var elements = document.querySelectorAll('button, a, [role="menuitem"], [role="option"]');
            for (var el of elements) {
                var text = el.textContent.toLowerCase();
                if (text.includes('website') || text.includes('url') || text.includes('link')) {
                    el.click();
                    return 'clicked website';
                }
            }
            return 'no website option';
        })()
    """)
    time.sleep(2)

    # Find URL input and type
    url_json = json.dumps(url)
    await cdp_eval(ws, f"""
        (function() {{
            var inputs = document.querySelectorAll('input[type="text"], input[type="url"], input:not([type])');
            for (var input of inputs) {{
                if (input.offsetParent !== null) {{
                    input.focus();
                    input.value = {url_json};
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return 'typed url';
                }}
            }}
            return 'no input found';
        }})()
    """)
    time.sleep(1)

    # Press Enter or click Submit
    await cdp_eval(ws, """
        (function() {
            var btn = document.querySelector('button[type="submit"], button[aria-label="Submit"]');
            if (btn) { btn.click(); return 'clicked submit'; }
            return 'no submit';
        })()
    """)

async def main():
    # Connect to browser
    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    ws_url = None
    for t in targets:
        if "notebooklm" in t.get("url", "").lower():
            ws_url = t.get("webSocketDebuggerUrl")
            break

    if not ws_url:
        print("No NotebookLM tab found")
        return

    async with websockets.connect(ws_url) as ws:
        # Navigate to NotebookLM home
        await cdp_eval(ws, "window.location.href = 'https://notebooklm.google.com'")
        time.sleep(5)

        created_notebooks = []

        for notebook_info in NOTEBOOKS:
            notebook_id = await create_notebook(ws, notebook_info)
            if notebook_id:
                created_notebooks.append({
                    "id": notebook_id,
                    "name": notebook_info["name"],
                    "description": notebook_info["description"],
                    "sources": notebook_info["sources"]
                })

                # Add sources
                for source_url in notebook_info["sources"]:
                    await add_source(ws, notebook_id, source_url)
                    time.sleep(3)

                # Navigate back to home for next notebook
                await cdp_eval(ws, "window.location.href = 'https://notebooklm.google.com'")
                time.sleep(3)

        # Save notebook list
        print("\n\nCreated notebooks:")
        print(json.dumps(created_notebooks, indent=2))

        # Save to file
        with open("/home/projects/nexa/backend/notebooks.json", "w") as f:
            json.dump(created_notebooks, f, indent=2)
        print("\nSaved to notebooks.json")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
