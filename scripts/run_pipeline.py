"""Run the MVP mention pipeline: collect, classify, and summarize."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.classifier import classify_mentions
from app.collector import fetch_reddit_mentions
from app.data_store import ensure_mentions_schema, load_mentions, save_mentions
from app.summary import build_weekly_summary, load_weekly_summary, save_weekly_summary

MENTIONS_PATH = "data/mentions.csv"
SUMMARY_PATH = "data/weekly_summary.json"


def run() -> None:
    preserved_count = ensure_mentions_schema(MENTIONS_PATH)
    print(f"[pipeline] Mentions CSV schema ready with {preserved_count} existing row(s).")

    mentions = fetch_reddit_mentions(keyword="Pulsetto")
    if mentions:
        inserted_count = save_mentions(MENTIONS_PATH, mentions)
        print(f"[pipeline] Fetched {len(mentions)} mention(s), saved {inserted_count} new row(s).")
    else:
        print("[pipeline] No mentions fetched. Using existing CSV data for classification.")

    saved_mentions = load_mentions(MENTIONS_PATH)
    classified_mentions = classify_mentions(saved_mentions)
    summary = build_weekly_summary(classified_mentions)
    previous_summary = load_weekly_summary(SUMMARY_PATH)

    if not classified_mentions and previous_summary.get("total_mentions", 0) > 0:
        summary = previous_summary
        summary["refresh_status"] = "preserved_previous_summary_no_current_rows"
        print("[pipeline] No classified rows available; preserved previous non-empty summary.")
    else:
        summary["refresh_status"] = "ok"

    save_weekly_summary(SUMMARY_PATH, summary)

    print(
        f"[pipeline] Classified {len(classified_mentions)} mention(s) and wrote summary to {SUMMARY_PATH}."
    )


if __name__ == "__main__":
    run()
