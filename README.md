# Community-Led Growth Research — B2B SaaS

A research repository on Community-Led Growth (CLG) in B2B SaaS, built for
the 100Hires Junior Growth Analyst technical assignment. Goal: collect
evidence-backed research from operators who have actually built, scaled, or
run communities inside B2B SaaS companies — structured well enough to
support a real CLG playbook later.

## Project Overview

Community-led growth treats a product's user community as a primary growth
engine — driving acquisition (referrals, word of mouth), activation
(onboarding via peers, templates, ambassadors), engagement, retention,
advocacy, and in some cases direct monetization. It matters in B2B SaaS
specifically because community reduces CAC (peer-driven acquisition is
cheaper than paid), increases LTV (community-engaged users churn less), and
creates a moat competitors can't easily copy (relationships, not just
features).

## Research Objective

Most "community growth" content online is written by people who have never
operated a community at scale. This repo intentionally prioritizes
**operators over commentators** — people with a named, verifiable case
study (Notion's Ambassador Program, Salesforce Trailblazer Community,
Common Room's own GTM, etc.) over generic LinkedIn thought-leadership
accounts. See `research/sources.md` for the full roster and selection
rationale per person.

## Methodology

Data is collected through a mix of API automation and manual collection,
documented honestly rather than glossed over:

- **YouTube:** `youtube-transcript-api` (free) for transcripts, YouTube
  Data API v3 (`playlistItems` on each channel's uploads playlist) for
  video metadata. Supadata is wired in as a fallback transcript source.
- **LinkedIn:** LinkedIn has no public API for reading another user's post
  history, and automated scraping violates LinkedIn's Terms of Service —
  so this is **manual collection**, structured automatically by
  `scripts/format_linkedin_post.py` so it lands in the same folder
  structure as everything else, with consistent metadata per post.
- **Manual verification:** every expert's current role/company was
  spot-checked before being added to the roster (see `notes` field in
  `config/experts.json`) — affiliations in this space change fast.

## Repository Structure

```
/research
  /research/sources.md                       # Full expert roster + rationale
  /research/linkedin-posts/<expert-id>/       # Manually collected posts, one .md per post
  /research/youtube-transcripts/<expert-id>/  # API-collected transcripts, one .md per video
  /research/other/                            # Podcast notes, anything else collected
  /research/analysis/
    community-growth-frameworks.md            # Named, repeatable frameworks found
    expert-comparison.md                      # 1-10 scoring matrix across 6 CLG dimensions
    key-insights.md                           # Answers to the core research questions
/config/experts.json                          # Single source of truth for the roster
/scripts/                                     # All collection + automation code
README.md
```

## Key Research Questions

- How do SaaS companies build communities from zero?
- How do communities measurably drive retention?
- How do communities create product adoption and reduce time-to-value?
- How do communities reduce CAC?
- How do communities increase LTV?
- Which tactics are broadly agreed upon vs. contrarian/unique to one operator?

## Expected Outcomes

Once `research/analysis/` is fully populated from the collected transcripts
and posts, this repo should support drafting a complete CLG playbook:
stage-by-stage tactics (acquisition → monetization), a scoring rubric for
evaluating a company's own community maturity, and a shortlist of
proven frameworks with named sources — not generic advice.

---

## Dashboard (Streamlit)

A control-panel UI sits on top of the same scripts above — left panel for
collection config, right panel for live scraped output:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

- **YouTube (API) mode** — pick an expert, paste a `@handle` (or rely on a
  saved `youtube_channel_id`), enter your API key, set how many videos, hit
  **Run Collection**. Status pills update live; results land in a table
  with a transcript preview; files are written to
  `research/youtube-transcripts/<expert-id>/` exactly as the CLI would.
- **LinkedIn (manual entry) mode** — same glass-panel form, but for pasting
  in a post you copied by hand. This is intentionally not a scraper (see
  Methodology above) — the dashboard just makes manual entry as fast as
  automation would be.

Your API keys are only held in the browser session for that run — they are
not written to disk unless you also fill in `.env` yourself.

## Technical Execution — How to Run This (CLI)


### 1. Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# then fill in YOUTUBE_API_KEY (free, from Google Cloud Console)
```

### 2. Resolve YouTube channel IDs (one-time, per expert)

`config/experts.json` ships with `youtube_channel_id: null` for most
experts — fill these in before pulling videos:

```bash
python scripts/resolve_channel.py --handle benln
# paste the returned channel_id into config/experts.json
```

### 3. Run the full YouTube pipeline

```bash
python scripts/run_pipeline.py --max-results 5
```

This fetches the latest 5 videos per expert (metadata via YouTube Data API
v3) and their transcripts (free method, with Supadata as automatic
fallback), writing markdown files into `research/youtube-transcripts/`.

Run the two steps separately if you want more control:

```bash
python scripts/fetch_youtube_videos.py --max-results 5 --expert ben-lang
python scripts/fetch_transcripts.py --expert ben-lang --source free
```

### 4. Collect LinkedIn posts (manual, structured)

```bash
python scripts/format_linkedin_post.py --expert ben-lang
```

Prompts for URL, date, topic, engagement, full text, and a takeaway, then
files it correctly. Repeat per post — aim for 10+ per expert per the brief.

### 5. Regenerate sources.md after any roster edit

```bash
python scripts/generate_sources_md.py
```

### Rate limits & quota notes

- YouTube Data API v3 has a default daily quota of 10,000 units;
  `playlistItems.list` costs 1 unit/call, so this is cheap even across 10
  experts. `search.list` costs 100 units/call — avoided here on purpose.
- `youtube-transcript-api` scrapes YouTube's caption endpoint directly and
  can be rate-limited or IP-blocked under heavy use — the pipeline adds a
  1-second delay between requests and falls back to Supadata automatically
  if configured.
- LinkedIn is **not** scraped, by design — see Methodology above.

### Commit discipline

Per the assignment brief, commit incrementally rather than one giant
commit: e.g. one commit per expert added to `experts.json`, one commit per
pipeline run, one commit per analysis file filled in.
