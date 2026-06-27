"""
generate_sources_md.py

Builds research/sources.md directly from config/experts.json, so the
roster file is always the single source of truth (edit the JSON, re-run
this, never hand-edit sources.md).

Usage:
    python scripts/generate_sources_md.py
"""

from datetime import date

from utils import load_experts, write_markdown, ROOT_DIR


def main():
    experts = load_experts()
    today = date.today().isoformat()

    lines = [
        "# Sources — Community-Led Growth Expert Roster\n",
        f"_Last generated: {today}_\n",
        "Selection criteria: real operating experience building, scaling, or "
        "running a community inside a B2B SaaS company — not general "
        "marketing commentary. Each entry below was checked against current "
        "public role/affiliation at the time of collection (roles in this "
        "space change quickly; re-verify before relying on this for a live "
        "submission).\n",
        "---\n",
    ]

    for e in experts:
        lines.append(f"## {e['name']}\n")
        lines.append(f"- **Role:** {e['role']}")
        lines.append(f"- **Company:** {e['company']}")
        lines.append(f"- **Category:** {e['category']}")
        lines.append(f"- **Why selected:** {e['why_selected']}")
        links = []
        if e.get("linkedin_url"):
            links.append(f"[LinkedIn]({e['linkedin_url']})")
        if e.get("website_url"):
            links.append(f"[Website]({e['website_url']})")
        if links:
            lines.append(f"- **Links:** {' · '.join(links)}")
        if e.get("notes"):
            lines.append(f"- **Research notes:** {e['notes']}")
        lines.append(f"- **Date collected:** {today}")
        lines.append("")

    content = "\n".join(lines)
    out_path = ROOT_DIR / "research" / "sources.md"
    write_markdown(out_path, content)


if __name__ == "__main__":
    main()
