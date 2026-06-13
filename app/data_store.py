"""Read and write feedback monitor mention data."""

from __future__ import annotations

import csv
from pathlib import Path

MENTIONS_COLUMNS = [
    "title",
    "body_text",
    "subreddit",
    "author",
    "created_date",
    "url",
    "source",
]

LEGACY_COLUMN_MAP = {
    "text": "body_text",
    "timestamp": "created_date",
    "channel": "source",
}


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    """Return a row containing expected columns with safe string values."""
    normalized: dict[str, str] = {}
    for column in MENTIONS_COLUMNS:
        value = row.get(column, "")
        normalized[column] = "" if value is None else str(value).strip()

    for legacy_column, target_column in LEGACY_COLUMN_MAP.items():
        if normalized[target_column]:
            continue
        legacy_value = row.get(legacy_column, "")
        normalized[target_column] = "" if legacy_value is None else str(legacy_value).strip()

    return normalized


def load_mentions(csv_path: str) -> list[dict[str, str]]:
    """Load mention rows from CSV if it exists."""
    path = Path(csv_path)
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [_normalize_row(row) for row in reader]


def ensure_mentions_schema(csv_path: str) -> int:
    """Create or repair the mentions CSV so future runs use the expected schema.

    Returns the number of rows preserved from the existing file.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        rows: list[dict[str, str]] = []
    else:
        rows = load_mentions(str(path))
        with path.open("r", newline="", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            current_header = next(reader, [])

        if current_header == MENTIONS_COLUMNS:
            return len(rows)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MENTIONS_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def save_mentions(csv_path: str, incoming_rows: list[dict[str, str]]) -> int:
    """Append new unique rows into the CSV and return inserted count.

    Rows are deduplicated by URL against existing records and within incoming_rows.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_mentions_schema(str(path))

    existing_rows = load_mentions(str(path))
    seen_urls = {row.get("url", "") for row in existing_rows if row.get("url")}
    final_rows = list(existing_rows)

    inserted = 0
    for row in incoming_rows:
        normalized = _normalize_row(row)
        url = normalized["url"]

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        final_rows.append(normalized)
        inserted += 1

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MENTIONS_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(final_rows)

    return inserted
