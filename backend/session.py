"""Server-side NotebookLM session using Chrome profile."""
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

CHROME_PROFILE = Path("/home/projects/nexa/data/chrome-profile")


class ServerSessionService:
    def __init__(self):
        self._initialized = False

    async def initialize(self) -> bool:
        self._initialized = True
        logger.info(f"Chrome profile: {CHROME_PROFILE}")
        return True

    async def is_session_valid(self) -> bool:
        """Check if Chrome profile has valid Google cookies."""
        db = CHROME_PROFILE / "Default" / "Cookies"
        if not db.exists():
            return False
        try:
            conn = sqlite3.connect(str(db))
            rows = conn.execute(
                "SELECT name FROM cookies WHERE host_key LIKE '%google%' AND name IN ('SID','HSID','APISID','SAPISID')"
            ).fetchall()
            conn.close()
            valid = len(rows) >= 3
            logger.info(f"Session check: {len(rows)} auth cookies found, valid={valid}")
            return valid
        except Exception as e:
            logger.error(f"Session check failed: {e}")
            return False

    async def close(self):
        self._initialized = False


server_session = ServerSessionService()
