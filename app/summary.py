"""Generate weekly summaries from classified mentions."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ISSUE_STAGE_MAP: dict[str, str] = {
    "support_silence": "support_aftercare",
    "poor_support_quality": "support_aftercare",
    "no_results": "first_use",
    "weak_results": "first_use",
    "onboarding_confusion": "setup",
    "app_connectivity": "setup",
    "comfort_fit": "first_use",
    "price_value_mismatch": "purchase",
    "trust_skepticism": "discovery",
    "scientific_credibility": "discovery",
    "delivery_logistics": "purchase",
    "pre_purchase_question": "discovery",
    "usage_question": "setup",
    "general_awareness": "discovery",
    "experience_sharing": "support_aftercare",
    "recommendation_seeking": "discovery",
    "positive_advocacy": "support_aftercare",
    "competitor_comparison": "discovery",
    "other": "discovery",
}

TRUST_RISK_CATEGORIES = {"trust_skepticism", "scientific_credibility", "support_silence", "no_results"}


def _safe_text(row: dict[str, str], limit: int = 220) -> str:
    text = " ".join([row.get("title", ""), row.get("body_text", "")]).strip()
    return text[:limit]


def _build_signal_items(rows: list[dict[str, str]], *, max_items: int = 5) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for row in rows[:max_items]:
        items.append(
            {
                "text": _safe_text(row),
                "issue_category": row.get("issue_category", "other"),
                "severity": row.get("severity", "low"),
                "source": row.get("source", ""),
                "url": row.get("url", ""),
            }
        )
    return items


def _trust_risk_score(classified_mentions: list[dict[str, str]], issue_counts: Counter[str]) -> int:
    total = len(classified_mentions)
    if total == 0:
        return 0

    negative_count = sum(1 for row in classified_mentions if row.get("sentiment") == "negative")
    high_severity_count = sum(1 for row in classified_mentions if row.get("severity") in {"high", "critical"})
    trust_issue_count = sum(issue_counts.get(category, 0) for category in TRUST_RISK_CATEGORIES)

    negative_share = negative_count / total
    high_severity_share = high_severity_count / total
    trust_issue_share = trust_issue_count / total

    weighted_score = (negative_share * 0.45) + (high_severity_share * 0.25) + (trust_issue_share * 0.30)
    return min(100, round(weighted_score * 100))


def build_weekly_summary(classified_mentions: list[dict[str, str]]) -> dict[str, Any]:
    """Build an MVP summary payload from classified mentions."""
    issue_counts = Counter(row.get("issue_category", "other") or "other" for row in classified_mentions)
    attribute_counts = Counter(row.get("attribute_affected", "other") or "other" for row in classified_mentions)
    source_breakdown = Counter((row.get("source", "unknown") or "unknown").lower() for row in classified_mentions)

    stage_breakdown = Counter(
        ISSUE_STAGE_MAP.get(row.get("issue_category", "other") or "other", "discovery")
        for row in classified_mentions
    )

    negative_mentions = [row for row in classified_mentions if row.get("sentiment", "") == "negative"]
    critical_mentions = [
        row for row in classified_mentions if row.get("severity", "") in {"high", "critical"} or row.get("sentiment", "") == "negative"
    ]

    top_critical_mentions = _build_signal_items(critical_mentions, max_items=5)

    top_positive_rows = [
        row
        for row in classified_mentions
        if row.get("sentiment") == "positive" or row.get("issue_category") == "positive_advocacy"
    ]
    top_negative_rows = [
        row
        for row in classified_mentions
        if row.get("sentiment") == "negative" or row.get("severity") in {"high", "critical"}
    ]

    trust_risk_score = _trust_risk_score(classified_mentions, issue_counts)
    support_gap_count = issue_counts.get("support_silence", 0) + issue_counts.get("poor_support_quality", 0)

    recommended_actions = [
        "Prioritize support backlog cleanup and enforce a 24-hour first-response SLA.",
        "Publish clearer setup and app troubleshooting guidance to reduce first-week friction.",
        "Address trust questions with transparent evidence, expectations, and side-by-side comparisons.",
    ]

    return {
        "total_mentions": len(classified_mentions),
        "negative_mentions": len(negative_mentions),
        "issue_category_counts": dict(issue_counts),
        "attribute_counts": dict(attribute_counts),
        "source_breakdown": dict(source_breakdown),
        "stage_breakdown": dict(stage_breakdown),
        "trust_risk_score": trust_risk_score,
        "support_gap_count": support_gap_count,
        "top_positive_signals": _build_signal_items(top_positive_rows, max_items=5),
        "top_negative_signals": _build_signal_items(top_negative_rows, max_items=5),
        "top_critical_mentions": top_critical_mentions,
        "recommended_actions": recommended_actions,
    }


def load_weekly_summary(input_path: str) -> dict[str, Any]:
    """Load an existing summary JSON file if it is present and valid."""
    path = Path(input_path)
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def save_weekly_summary(output_path: str, summary: dict[str, Any]) -> None:
    """Persist summary JSON to disk."""
    summary["last_refreshed_at"] = datetime.now(timezone.utc).isoformat()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as json_file:
        json.dump(summary, json_file, indent=2)
        json_file.write("\n")
