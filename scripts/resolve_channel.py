"""
resolve_channel.py

YouTube Data API v3 requires a channel_id for most reliable lookups, but
people usually give you a handle (@username) or a custom URL. This script
resolves a handle -> channel_id and -> the channel's "uploads" playlist ID,
then prints a JSON snippet you can paste into config/experts.json.

Usage:
    python scripts/resolve_channel.py --handle benln
    python scripts/resolve_channel.py --handle "@CommonRoomHQ"

Requires:
    YOUTUBE_API_KEY in .env (see .env.example)
"""

import argparse
import json
import os
import sys

import requests

from utils import load_env, log

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def resolve_handle(handle: str, api_key: str) -> dict:
    handle = handle.lstrip("@")
    params = {
        "part": "snippet,contentDetails",
        "forHandle": handle,
        "key": api_key,
    }
    resp = requests.get(f"{YOUTUBE_API_BASE}/channels", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("items"):
        raise ValueError(f"No channel found for handle '@{handle}'. Double-check the handle.")

    item = data["items"][0]
    channel_id = item["id"]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    title = item["snippet"]["title"]

    return {
        "channel_title": title,
        "channel_id": channel_id,
        "uploads_playlist_id": uploads_playlist_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Resolve a YouTube handle to a channel ID.")
    parser.add_argument("--handle", required=True, help="YouTube handle, e.g. @benln or benln")
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        log.error("YOUTUBE_API_KEY not set. Add it to your .env file (see .env.example).")
        sys.exit(1)

    try:
        result = resolve_handle(args.handle, api_key)
    except Exception as e:
        log.error(str(e))
        sys.exit(1)

    log.info(f"Resolved '@{args.handle.lstrip('@')}' -> {result['channel_title']}")
    print(json.dumps(result, indent=2))
    print(
        "\nPaste channel_id into the matching expert's "
        "\"youtube_channel_id\" field in config/experts.json"
    )


if __name__ == "__main__":
    main()
