"""
utils.py
Shared helpers used by every script in this pipeline.
"""

import json
import os
import re
import time
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "experts.json"
YOUTUBE_TRANSCRIPTS_DIR = ROOT_DIR / "research" / "youtube-transcripts"
LINKEDIN_POSTS_DIR = ROOT_DIR / "research" / "linkedin-posts"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("clg-pipeline")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
def load_experts():
    """Load the expert roster from config/experts.json."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["experts"]


def slugify(name: str) -> str:
    """Turn 'Linda Lian' into 'linda-lian' for folder/file names."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------
def ensure_expert_dirs(expert_id: str):
    """Create the per-expert folders under research/ if they don't exist."""
    yt_dir = YOUTUBE_TRANSCRIPTS_DIR / expert_id
    li_dir = LINKEDIN_POSTS_DIR / expert_id
    yt_dir.mkdir(parents=True, exist_ok=True)
    li_dir.mkdir(parents=True, exist_ok=True)
    return yt_dir, li_dir


def write_markdown(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    log.info(f"Wrote {path.relative_to(ROOT_DIR)}")


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
def polite_sleep(seconds: float = 1.0):
    """Small delay between API calls so we don't hammer rate limits."""
    time.sleep(seconds)


# ---------------------------------------------------------------------------
# Env loading (no external dependency required)
# ---------------------------------------------------------------------------
def load_env(env_path: Path = None):
    """
    Minimal .env loader so we don't require python-dotenv.
    Reads KEY=VALUE lines from .env and injects them into os.environ
    (without overwriting variables already set in the shell).
    """
    env_path = env_path or (ROOT_DIR / ".env")
    if not env_path.exists():
        log.warning(f".env not found at {env_path} — relying on shell environment variables only.")
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
