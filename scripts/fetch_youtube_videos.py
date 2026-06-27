"""
fetch_youtube_videos.py

Pulls the latest N videos for every expert in config/experts.json that has
a youtube_channel_id set, using the YouTube Data API v3 (playlistItems on
the channel's "uploads" playlist — cheaper on quota than search.list).

Output: scripts/.cache/videos_<expert_id>.json
        (raw API output, consumed later by fetch_transcripts.py)

Usage:
    python scripts/fetch_youtube_videos.py --max-results 5
    python scripts/fetch_youtube_videos.py --expert ben-lang --max-results 5

Requires:
    YOUTUBE_API_KEY in .env
    pip install requests
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

from utils import load_env, load_experts, polite_sleep, log, ROOT_DIR

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
CACHE_DIR = ROOT_DIR / "scripts" / ".cache"


def get_uploads_playlist_id(channel_id: str, api_key: str) -> str:
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    resp = requests.get(f"{YOUTUBE_API_BASE}/channels", params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"No channel found for channel_id={channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_latest_videos(uploads_playlist_id: str, api_key: str, max_results: int = 5):
    params = {
        "part": "snippet,contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": min(max_results, 50),
        "key": api_key,
    }
    resp = requests.get(f"{YOUTUBE_API_BASE}/playlistItems", params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("items", [])

    videos = []
    for item in items[:max_results]:
        snippet = item["snippet"]
        video_id = item["contentDetails"]["videoId"]
        videos.append(
            {
                "video_id": video_id,
                "title": snippet.get("title"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description", "")[:500],
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
    return videos


def main():
    parser = argparse.ArgumentParser(description="Fetch latest videos per expert via YouTube Data API v3.")
    parser.add_argument("--max-results", type=int, default=5, help="Videos per expert (default 5)")
    parser.add_argument("--expert", default=None, help="Limit to a single expert id (e.g. ben-lang)")
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        log.error("YOUTUBE_API_KEY not set. Add it to your .env file (see .env.example).")
        sys.exit(1)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    experts = load_experts()
    if args.expert:
        experts = [e for e in experts if e["id"] == args.expert]
        if not experts:
            log.error(f"No expert with id '{args.expert}' in config/experts.json")
            sys.exit(1)

    for expert in experts:
        channel_id = expert.get("youtube_channel_id")
        if not channel_id:
            log.warning(f"Skipping {expert['name']} — no youtube_channel_id set. "
                        f"Run resolve_channel.py first if they have a channel.")
            continue

        try:
            log.info(f"Fetching uploads playlist for {expert['name']}...")
            uploads_playlist_id = get_uploads_playlist_id(channel_id, api_key)
            polite_sleep(0.5)

            log.info(f"Fetching latest {args.max_results} videos for {expert['name']}...")
            videos = fetch_latest_videos(uploads_playlist_id, api_key, args.max_results)
            polite_sleep(0.5)

            out_path = CACHE_DIR / f"videos_{expert['id']}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"expert_id": expert["id"], "videos": videos}, f, indent=2)
            log.info(f"Saved {len(videos)} videos -> {out_path.relative_to(ROOT_DIR)}")

        except requests.HTTPError as e:
            log.error(f"YouTube API error for {expert['name']}: {e}")
        except Exception as e:
            log.error(f"Failed to fetch videos for {expert['name']}: {e}")


if __name__ == "__main__":
    main()
