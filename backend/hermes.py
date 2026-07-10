import httpx
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

LLM_ENDPOINT = "https://llm2.jugaar.ai/v1/chat/completions"
LLM_MODEL = "xiaomimimo/mimo-v2.5"
LLM_API_KEY = "sk-proxy-332b060b9f745295593f5bca63d7c0b52aeac5b0821aebb9"

# Load notebooks
NOTEBOOKS_PATH = Path(__file__).parent / "notebooks.json"
try:
    NOTEBOOKS = json.loads(NOTEBOOKS_PATH.read_text())
except Exception:
    NOTEBOOKS = []

NOTEBOOK_LIST = "\n".join([
    f"{i+1}. {nb['name']} (id: {nb['id']}) - {nb['description']}"
    for i, nb in enumerate(NOTEBOOKS)
])

SYSTEM_PROMPT = f"""You are Nexa, a NotebookLM assistant. Your job is to:
1. Analyze the user's query
2. Pick the MOST relevant notebook from the list below
3. Refine the prompt for that notebook
4. Return ONLY valid JSON

Available Notebooks:
{NOTEBOOK_LIST}

Rules:
1. Pick the notebook that BEST matches the user's topic
2. If the user writes in Roman Urdu/Hindi/non-English, translate to clear English
3. Refine the prompt to be clear, specific, and well-structured
4. If the user provides a URL, include it in the refined prompt
5. Return ONLY valid JSON in this exact format: {{"notebook_id": "...", "query": "..."}}
6. Do NOT add any explanation, prefixes, or text outside the JSON

Examples:
Input: "meri website ka sitemap banao"
Output: {{"notebook_id": "{NOTEBOOKS[4]['id'] if len(NOTEBOOKS) > 4 else '...'}", "query": "Create a sitemap for my website. Please provide the URL and I will generate a structured sitemap."}}

Input: "explain quantum computing simply"
Output: {{"notebook_id": "{NOTEBOOKS[0]['id'] if NOTEBOOKS else '...'}", "query": "Explain quantum computing in simple terms, covering the basic concepts of qubits, superposition, and entanglement."}}

Input: "who was Napoleon"
Output: {{"notebook_id": "{NOTEBOOKS[1]['id'] if len(NOTEBOOKS) > 1 else '...'}", "query": "Provide a comprehensive overview of Napoleon Bonaparte, including his rise to power, major achievements, military campaigns, and legacy."}}
"""


async def refine_prompt(user_message: str) -> dict:
    """Send user message to Hermes and get notebook selection + refined prompt."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LLM_ENDPOINT,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LLM_API_KEY}",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 512,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Hermes raw: '{content[:100]}...'")

            # Parse JSON response
            try:
                # Strip markdown code blocks if present
                clean = content
                if "```" in clean:
                    # Extract content between ``` markers
                    import re
                    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', clean, re.DOTALL)
                    if match:
                        clean = match.group(1).strip()
                result = json.loads(clean)
                notebook_id = result.get("notebook_id", NOTEBOOKS[0]["id"] if NOTEBOOKS else "")
                query = result.get("query", user_message)
                logger.info(f"Hermes refined: notebook={notebook_id[:8]}... query='{query[:60]}...'")
                return {"notebook_id": notebook_id, "query": query}
            except json.JSONDecodeError:
                # Fallback: return first notebook with original message
                logger.warning(f"Failed to parse Hermes JSON, using fallback")
                return {
                    "notebook_id": NOTEBOOKS[0]["id"] if NOTEBOOKS else "",
                    "query": content
                }
    except Exception as e:
        logger.error(f"Hermes refinement failed: {e}")
        return {
            "notebook_id": NOTEBOOKS[0]["id"] if NOTEBOOKS else "",
            "query": user_message
        }
