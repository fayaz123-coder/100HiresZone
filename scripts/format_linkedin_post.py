"""
format_linkedin_post.py

LinkedIn has no public API for reading another user's post history, and
automated scraping of LinkedIn violates its Terms of Service / anti-bot
protections — so this is intentionally NOT a scraper. Instead, this is the
"manual collection, structured automatically" half of the brief: you paste
in what you copied by hand, and this script formats and files it correctly
under research/linkedin-posts/<expert-id>/ so the repo stays consistent.

Usage (interactive):
    python scripts/format_linkedin_post.py --expert ben-lang

You'll be prompted for: URL, date, post text, engagement metrics, and a
one-line takeaway. Repeat once per post (aim for the brief's minimum of
10 posts/expert).
"""

import argparse
import sys
from datetime import datetime

from utils import load_experts, ensure_expert_dirs, write_markdown, slugify, log


def prompt(label: str, multiline: bool = False) -> str:
    if multiline:
        print(f"{label} (end input with a single line containing only 'END'):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
    return input(f"{label}: ").strip()


def main():
    parser = argparse.ArgumentParser(description="File a manually-collected LinkedIn post into the repo.")
    parser.add_argument("--expert", required=True, help="Expert id from config/experts.json")
    args = parser.parse_args()

    experts = {e["id"]: e for e in load_experts()}
    if args.expert not in experts:
        log.error(f"No expert with id '{args.expert}' in config/experts.json")
        sys.exit(1)
    expert = experts[args.expert]

    _, li_dir = ensure_expert_dirs(args.expert)

    print(f"\nFiling a LinkedIn post for {expert['name']}\n")
    post_url = prompt("Post URL")
    post_date = prompt("Post date (YYYY-MM-DD)")
    topic_category = prompt("Topic category (e.g. retention, advocacy, monetization)")
    engagement = prompt("Engagement metrics if visible (likes/comments/reposts, or 'n/a')")
    post_text = prompt("Paste the post text", multiline=True)
    takeaway = prompt("One-line key takeaway")

    slug_date = post_date.replace("-", "") if post_date else datetime.now().strftime("%Y%m%d")
    filename = f"{slug_date}-{slugify(post_url.split('/')[-1] or 'post')[:40]}.md"

    md = f"""# LinkedIn Post — {expert['name']}

- **URL:** {post_url}
- **Date:** {post_date}
- **Topic category:** {topic_category}
- **Engagement:** {engagement}

## Post Text

{post_text}

## Key Takeaway

{takeaway}
"""
    out_path = li_dir / filename
    write_markdown(out_path, md)
    log.info(f"Filed. {len(list(li_dir.glob('*.md')))} posts collected so far for {expert['name']}.")


if __name__ == "__main__":
    main()
