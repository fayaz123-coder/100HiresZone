"""
run_pipeline.py

One command to run the full YouTube collection pipeline:
  1. fetch latest videos for every expert with a channel_id set
  2. fetch transcripts for all of them
  3. print a short summary report

This is what you'd point a hiring manager at to demonstrate the API
workflow end-to-end.

Usage:
    python scripts/run_pipeline.py --max-results 5
"""

import argparse
import subprocess
import sys
from pathlib import Path

from utils import log, ROOT_DIR


def run(cmd: list):
    log.info(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        log.error(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the full YouTube collection pipeline.")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--source", choices=["free", "supadata"], default="free")
    args = parser.parse_args()

    python = sys.executable

    run([python, "scripts/fetch_youtube_videos.py", "--max-results", str(args.max_results)])
    run([python, "scripts/fetch_transcripts.py", "--source", args.source])

    transcripts_dir = ROOT_DIR / "research" / "youtube-transcripts"
    total_files = sum(1 for _ in transcripts_dir.rglob("*.md"))
    log.info(f"Pipeline complete. {total_files} transcript files written under research/youtube-transcripts/")


if __name__ == "__main__":
    main()
