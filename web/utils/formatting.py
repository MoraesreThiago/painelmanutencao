from __future__ import annotations

from datetime import datetime


def humanize(value: str | None) -> str:
    if not value:
        return "-"
    return value.replace("_", " ").strip().title()


def short_datetime(value: str | None) -> str:
    if not value:
        return "-"
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value.replace("T", " ")[:16]
    return parsed.strftime("%d/%m/%Y %H:%M")


def month_start() -> datetime:
    now = datetime.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None

