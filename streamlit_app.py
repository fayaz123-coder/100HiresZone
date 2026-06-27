"""
streamlit_app.py

A control-panel UI for the CLG research pipeline:
  LEFT  — configuration (which expert, which source, API key, how many items)
  RIGHT — live output (status log, results table, transcript preview, download)

This is a UI layer on top of the scripts you already have in /scripts —
it does not replace them, it calls the same functions so behaviour stays
identical whether you run from the CLI or this dashboard.

Run with:
    streamlit run streamlit_app.py
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from utils import load_experts, ensure_expert_dirs, write_markdown, slugify  # noqa: E402
from fetch_youtube_videos import get_uploads_playlist_id, fetch_latest_videos  # noqa: E402
from fetch_transcripts import fetch_transcript_free, fetch_transcript_supadata, build_markdown  # noqa: E402
from resolve_channel import resolve_handle  # noqa: E402

st.set_page_config(
    page_title="CLG Research Console",
    page_icon="\U0001F311",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Premium glassmorphism styling — night sky + lavender field mood,
# built entirely in CSS (gradients + box-shadow stars), no external image.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Night-sky + lavender-field backdrop, pure CSS */
    .stApp {
        background:
            radial-gradient(ellipse 60% 40% at 50% 0%, rgba(167,139,250,0.18), transparent 60%),
            linear-gradient(180deg, #0b0a18 0%, #1b1733 28%, #3a2f5c 52%, #5b4a86 68%, #2a2240 100%);
        background-attachment: fixed;
    }

    /* scattered "stars" */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            radial-gradient(1.5px 1.5px at 10% 15%, #fff, transparent),
            radial-gradient(1px 1px at 25% 8%, #fff, transparent),
            radial-gradient(1.5px 1.5px at 40% 22%, #fff, transparent),
            radial-gradient(1px 1px at 60% 5%, #fff, transparent),
            radial-gradient(1.5px 1.5px at 75% 18%, #fff, transparent),
            radial-gradient(1px 1px at 90% 10%, #fff, transparent),
            radial-gradient(1.5px 1.5px at 15% 35%, #fff, transparent),
            radial-gradient(1px 1px at 80% 30%, #fff, transparent);
        opacity: 0.6;
        pointer-events: none;
        z-index: 0;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 18px;
        padding: 1.6rem 1.6rem 1.2rem 1.6rem;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #ffffff 0%, #c9b8ff 60%, #a78bfa 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .hero-sub {
        text-align: center;
        color: rgba(237,235,245,0.65);
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
    }

    .panel-label {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #c9b8ff;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }

    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 10px !important;
        color: #EDEBF5 !important;
    }

    /* Primary button — pill, light, like the "Log In" button in the reference */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #f5f3ff, #e4dcff);
        color: #221a3d;
        border: none;
        border-radius: 999px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: transform 0.15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(167,139,250,0.35);
    }

    /* Status pill */
    .status-pill {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .status-ok   { background: rgba(74, 222, 128, 0.18); color: #4ade80; }
    .status-warn { background: rgba(250, 204, 21, 0.18); color: #facc15; }
    .status-err  { background: rgba(248, 113, 113, 0.18); color: #f87171; }

    section[data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">Welcome back, researcher.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Configure a collection run on the left — watch results land on the right.</div>',
    unsafe_allow_html=True,
)

if "results" not in st.session_state:
    st.session_state.results = []  # list of dicts: title, url, published_at, transcript_status, transcript
if "log" not in st.session_state:
    st.session_state.log = []

experts = load_experts()
expert_names = [e["name"] for e in experts]
expert_by_name = {e["name"]: e for e in experts}

left, right = st.columns([1, 1.4], gap="large")

# ---------------------------------------------------------------------------
# LEFT — configuration panel
# ---------------------------------------------------------------------------
with left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Collection Configuration</div>', unsafe_allow_html=True)

    expert_name = st.selectbox("Expert", expert_names)
    selected = expert_by_name[expert_name]

    source_mode = st.radio(
        "Source",
        ["YouTube (API)", "LinkedIn (manual entry)"],
        help="LinkedIn has no public API for reading another user's posts and "
             "automated scraping violates its Terms of Service, so that path "
             "is manual-entry-only, formatted to match the rest of the repo.",
    )

    st.divider()

    if source_mode == "YouTube (API)":
        api_key = st.text_input("YouTube Data API Key", type="password",
                                 help="Free from Google Cloud Console — enable 'YouTube Data API v3'.")
        handle = st.text_input(
            "Channel handle (optional)",
            placeholder="@channelhandle",
            help="Only needed if this expert's channel_id isn't already saved in config/experts.json.",
        )
        channel_id_existing = selected.get("youtube_channel_id")
        if channel_id_existing:
            st.caption(f"Using saved channel_id: `{channel_id_existing}`")

        max_results = st.slider("Videos to fetch", min_value=1, max_value=15, value=5)
        transcript_source = st.radio("Transcript source", ["free", "supadata"], horizontal=True)
        supadata_key = None
        if transcript_source == "supadata":
            supadata_key = st.text_input("Supadata API Key", type="password")

        run_clicked = st.button("Run Collection")

    else:
        st.caption(f"Filing a manually-collected post for **{expert_name}**")
        post_url = st.text_input("Post URL")
        post_date = st.text_input("Post date (YYYY-MM-DD)")
        topic_category = st.text_input("Topic category", placeholder="e.g. retention, advocacy")
        engagement = st.text_input("Engagement metrics", placeholder="likes / comments / reposts, or n/a")
        post_text = st.text_area("Post text", height=160)
        takeaway = st.text_input("Key takeaway")
        run_clicked = st.button("File Post")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# RIGHT — output panel
# ---------------------------------------------------------------------------
with right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Scraped Output</div>', unsafe_allow_html=True)

    log_box = st.empty()

    def render_log():
        pills = ""
        for lvl, m in st.session_state.log:
            cls = {"ok": "status-ok", "warn": "status-warn", "err": "status-err"}[lvl]
            pills += f'<div style="margin-bottom:0.3rem;"><span class="status-pill {cls}">{lvl.upper()}</span>{m}</div>'
        log_box.markdown(pills, unsafe_allow_html=True)

    def log(msg: str, level: str = "ok"):
        st.session_state.log.insert(0, (level, msg))
        st.session_state.log = st.session_state.log[:8]
        render_log()

    if not st.session_state.log:
        log("Idle — waiting for a run.", "ok")
    else:
        render_log()

    results_placeholder = st.container()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Run logic
# ---------------------------------------------------------------------------
if source_mode == "YouTube (API)" and run_clicked:
    if not api_key:
        log("YouTube API key is required.", "err")
    else:
        try:
            channel_id = channel_id_existing
            if handle:
                with st.spinner(f"Resolving handle @{handle.lstrip('@')}..."):
                    resolved = resolve_handle(handle, api_key)
                    channel_id = resolved["channel_id"]
                    log(f"Resolved @{handle.lstrip('@')} -> {resolved['channel_title']}", "ok")

            if not channel_id:
                log("No channel_id available — provide a handle or set one in config/experts.json.", "err")
            else:
                with st.spinner("Fetching uploads playlist..."):
                    uploads_playlist_id = get_uploads_playlist_id(channel_id, api_key)

                with st.spinner(f"Fetching latest {max_results} videos..."):
                    videos = fetch_latest_videos(uploads_playlist_id, api_key, max_results)
                log(f"Fetched {len(videos)} videos for {expert_name}.", "ok")

                rows = []
                yt_dir, _ = ensure_expert_dirs(selected["id"])
                progress = st.progress(0.0)

                for i, video in enumerate(videos):
                    transcript, used_source, status = "", transcript_source, "ok"
                    try:
                        if transcript_source == "free":
                            transcript = fetch_transcript_free(video["video_id"])
                        else:
                            if not supadata_key:
                                raise RuntimeError("Supadata key not provided")
                            transcript = fetch_transcript_supadata(video["video_id"], supadata_key)
                    except Exception as e:
                        status = "warn"
                        log(f"Transcript unavailable for '{video['title'][:40]}...' ({e})", "warn")

                    if transcript:
                        md = build_markdown(expert_name, video, transcript, used_source)
                        write_markdown(yt_dir / f"{video['video_id']}.md", md)

                    rows.append(
                        {
                            "Title": video["title"],
                            "Published": video.get("published_at", "")[:10],
                            "Transcript": "✅" if transcript else "—",
                            "URL": video["url"],
                        }
                    )
                    progress.progress((i + 1) / len(videos))
                    time.sleep(0.3)

                st.session_state.results = rows
                log(f"Saved {sum(1 for r in rows if r['Transcript']=='✅')} transcripts to "
                    f"research/youtube-transcripts/{selected['id']}/", "ok")

        except requests.HTTPError as e:
            log(f"YouTube API error: {e}", "err")
        except Exception as e:
            log(f"Run failed: {e}", "err")

elif source_mode == "LinkedIn (manual entry)" and run_clicked:
    if not post_url or not post_text:
        log("Post URL and post text are required.", "err")
    else:
        _, li_dir = ensure_expert_dirs(selected["id"])
        slug_date = post_date.replace("-", "") if post_date else "undated"
        filename = f"{slug_date}-{slugify(post_url.split('/')[-1] or 'post')[:40]}.md"
        md = f"""# LinkedIn Post — {expert_name}

- **URL:** {post_url}
- **Date:** {post_date}
- **Topic category:** {topic_category}
- **Engagement:** {engagement}

## Post Text

{post_text}

## Key Takeaway

{takeaway}
"""
        write_markdown(li_dir / filename, md)
        log(f"Filed post -> research/linkedin-posts/{selected['id']}/{filename}", "ok")
        st.session_state.results = [
            {"Title": f"LinkedIn post ({post_date or 'undated'})", "Published": post_date,
             "Transcript": "n/a", "URL": post_url}
        ]

# ---------------------------------------------------------------------------
# Render results table + transcript preview in the right panel
# ---------------------------------------------------------------------------
with results_placeholder:
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if source_mode == "YouTube (API)":
            titles = [r["Title"] for r in st.session_state.results]
            pick = st.selectbox("Preview a transcript", titles, key="preview_pick")
            picked = next((r for r in st.session_state.results if r["Title"] == pick), None)
            if picked:
                vid_id = picked["URL"].split("v=")[-1]
                preview_path = ROOT_DIR / "research" / "youtube-transcripts" / selected["id"] / f"{vid_id}.md"
                if preview_path.exists():
                    with st.expander("Transcript preview", expanded=False):
                        st.markdown(preview_path.read_text(encoding="utf-8")[:3000])
    else:
        st.caption("No results yet — configure a run on the left and click the button.")
