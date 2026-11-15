"""Abwesenheiten der Gildenmitglieder (D-N1 Wunsch 1, ab Bot 1.5.184) – reine Funktionen ohne Discord.

Gespeichert in state.json unter "absences": {"<Discord-ID>": [{"von": "JJJJ-MM-TT", "bis": "JJJJ-MM-TT",
"grund": "…"}]}. Nur Datum und optional ein kurzer Grund. Einträge, deren Ende vor heute liegt, laufen ab (prune).
Den Grund sehen nur das Mitglied selbst und die Gildenleitung; öffentlich (Raid-Anmeldung) erscheinen nur Namen.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import raidmaster_data as rmd

MAX_TAGE = 120          # eine Abwesenheit höchstens so lang (Tippfehler im Jahr fallen so auf)
MAX_VORAUS = 365        # Beginn höchstens so viele Tage in der Zukunft
MAX_EINTRAEGE = 5       # je Mitglied gleichzeitig
GRUND_MAX = 80          # Zeichen


def parse_range(von: str, bis: str, tz: str, now: datetime | None = None) -> tuple[date, date]:
    """'20.11.' / '20.11.2026' -> Datum. Ohne Jahr: dieses Jahr, liegt der Tag schon zurück, das nächste;
    ein Ende ohne Jahr vor dem Beginn gehört ins Folgejahr (z. B. 28.12. bis 03.01.)."""
    start = rmd.parse_datetime(von, "23:59", tz, now)
    end = rmd.parse_datetime(bis, "23:59", tz, start)
    return start.date(), end.date()


def clean_reason(text: str | None) -> str:
    """Eine Zeile, ohne Erwähnungen (@), höchstens GRUND_MAX Zeichen."""
    t = " ".join((text or "").split()).replace("@", "")
    return t[:GRUND_MAX]


def prune(data: dict, today: date) -> int:
    """Abgelaufene Einträge (Ende vor heute) löschen. Liefert die Zahl der gelöschten Einträge."""
    removed = 0
    for uid in list(data):
        keep = [e for e in data[uid] if date.fromisoformat(e["bis"]) >= today]
        removed += len(data[uid]) - len(keep)
        if keep:
            data[uid] = keep
        else:
            del data[uid]
    return removed


def add(data: dict, uid: int | str, start: date, end: date, reason: str | None, today: date) -> dict:
    """Neuen Eintrag anlegen. ValueError mit einer Meldung für das Mitglied, wenn etwas nicht passt."""
    if end < start:
        raise ValueError("Das Ende liegt vor dem Beginn.")
    if end < today:
        raise ValueError("Diese Abwesenheit liegt schon in der Vergangenheit.")
    if (end - start).days + 1 > MAX_TAGE:
        raise ValueError(f"Höchstens {MAX_TAGE} Tage am Stück – bitte das Jahr prüfen oder aufteilen.")
    if start > today + timedelta(days=MAX_VORAUS):
        raise ValueError("Der Beginn liegt mehr als ein Jahr in der Zukunft.")
    prune(data, today)
    entries = data.setdefault(str(uid), [])
    entry = {"von": start.isoformat(), "bis": end.isoformat(), "grund": clean_reason(reason)}
    if any(e["von"] == entry["von"] and e["bis"] == entry["bis"] for e in entries):
        raise ValueError("Diese Abwesenheit ist schon eingetragen.")
    if len(entries) >= MAX_EINTRAEGE:
        raise ValueError(f"Höchstens {MAX_EINTRAEGE} Abwesenheiten gleichzeitig – zuerst eine entfernen.")
    entries.append(entry)
    entries.sort(key=lambda e: (e["von"], e["bis"]))
    return entry


def remove(data: dict, uid: int | str, number: int) -> dict | None:
    """Eintrag Nummer `number` (1 = erster in der Liste) des Mitglieds löschen; None, wenn es ihn nicht gibt."""
    entries = data.get(str(uid)) or []
    if not 1 <= number <= len(entries):
        return None
    entry = entries.pop(number - 1)
    if not entries:
        data.pop(str(uid), None)
    return entry


def absent_on(data: dict, day: date) -> set[str]:
    """Discord-IDs (als Text) aller Mitglieder, die an diesem Tag abwesend gemeldet sind."""
    d = day.isoformat()
    return {uid for uid, entries in data.items() if any(e["von"] <= d <= e["bis"] for e in entries)}


def span_text(entry: dict) -> str:
    """'20.11.–27.11.2026' bzw. '28.12.2026–03.01.2027'; ein Tag: '20.11.2026'."""
    a, b = date.fromisoformat(entry["von"]), date.fromisoformat(entry["bis"])
    if a == b:
        return a.strftime("%d.%m.%Y")
    left = a.strftime("%d.%m.") if a.year == b.year else a.strftime("%d.%m.%Y")
    return f"{left}–{b.strftime('%d.%m.%Y')}"
