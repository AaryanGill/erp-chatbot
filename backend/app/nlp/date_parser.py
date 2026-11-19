"""
Extracts dates from free-text queries like:
  "apply leave from 5 Nov to 8 Nov"
  "apply leave on 12th December"
  "apply leave on 2026-11-20"
  "apply leave tomorrow"
Returns a list of date objects in the order they appear in the text.
"""

import re
from datetime import date, timedelta

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
MONTH_RE = "|".join(MONTHS.keys())


def _build_date(month: int, day: int, today: date):
    """Builds a date in the current year; if it already passed, uses next year."""
    try:
        d = date(today.year, month, day)
        if d < today:
            d = date(today.year + 1, month, day)
        return d
    except ValueError:
        return None  # e.g. 31 Feb


def extract_dates(query: str, today: date = None):
    today = today or date.today()
    q = query.lower()
    found = []  # list of (position_in_text, date)

    # Format 1: 2026-11-20
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", q):
        try:
            found.append((m.start(), date(int(m.group(1)), int(m.group(2)), int(m.group(3)))))
        except ValueError:
            pass

    # Format 2: 5 nov / 5th november
    for m in re.finditer(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTH_RE})[a-z]*\b", q):
        d = _build_date(MONTHS[m.group(2)], int(m.group(1)), today)
        if d:
            found.append((m.start(), d))

    # Format 3: nov 5 / november 5th
    for m in re.finditer(rf"\b({MONTH_RE})[a-z]*\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", q):
        d = _build_date(MONTHS[m.group(1)], int(m.group(2)), today)
        if d:
            found.append((m.start(), d))

    # Word: tomorrow
    idx = q.find("tomorrow")
    if idx != -1:
        found.append((idx, today + timedelta(days=1)))

    found.sort(key=lambda x: x[0])
    return [d for _, d in found]