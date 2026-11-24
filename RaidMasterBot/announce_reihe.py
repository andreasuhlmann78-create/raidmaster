"""Reihen und Fassungen der Ankündigungen (announce/) – EIN Ort für den Bot und die Discord-Prüfung (D-CHK1, ab Bot 1.5.194).

Ohne discord.py: discord-check/check.py lädt diese Datei direkt (GitHub-Workflow).

- announce_series(fn): Reihe und Version mit Punkt ("…-3.12.94.md", "…-1.8.md") – unverändert wie bisher im Bot
  (Bearbeiten statt neu posten, Aufräumen älterer Versionen, D-ANN2).
- fassung(fn): dazu auch Dateien OHNE Versionsnummer im Namen: "<kanal>__<name>.md" ist Fassung 1, "<kanal>__<name>-N.md"
  Fassung N (ganze Zahl). Reihe und Fassung mit Punkt-Version gehören zusammen: threatsentinel-0-vorstellung.md (1) ist älter als
  threatsentinel-0-vorstellung-2.2.md (2.2). Belegt an der Repo-Geschichte (24.11.): Bei allen Reihen ohne Punkt-Version kam die
  Datei mit der grösseren Zahl später dazu (BuffSentinel 0-vorstellung bis -12, GuildSentinel bis -19).
  Grund: Seit der Wiederherstellung vom 23.11. (33 Dateien) zeigt das Datum des letzten Commits nicht mehr, welche Fassung die
  neueste ist; die Nummer im Namen schon.
- aeltere(fns): alle Dateien, die eine neuere Fassung derselben Reihe neben sich haben. Die Prüfung prüft sie nicht (Info).
  Der Bot gibt sie beim Start nie zum Neu-Posten frei und bessert sie nie nach; ohne Punkt-Version postet er sie nie. Mit
  Punkt-Version gilt beim Posten wie bisher D-ANN2 (nie älter/gleich der neuesten geposteten) und "Ersetzen wie bisher".
  Gelöscht wird nichts (Entscheid des Nutzers 23.11. 11:36).
- ABGELOEST: Dateien ohne eigene neuere Fassung, deren Inhalt anderswo aktuell steht (Bericht RaidMaster 24.11. 10:30).
- split_parts(text): Text in Discord-Nachrichten <= 1900 Zeichen teilen – an Absätzen, ein zu langer Absatz an Zeilen
  (bis 1.5.193 wurde er bei 2000 Zeichen abgeschnitten: LevelPilot-Übersicht 3.12.94, 3 Zeilen fehlten im Discord).
"""
from __future__ import annotations

import re

ANNOUNCE_VER = re.compile(r"^(?P<series>.+?)[-_ ]v?(?P<ver>\d+(?:\.\d+)+)(?P<rest>.*)$")
FASSUNG_NR = re.compile(r"^(?P<series>.+?)-(?P<n>\d+)$")
PART_MAX = 1900

ABGELOEST = {
    "raid-addon-zusammenfassung-3.0.0.md": "abgelöst durch die Vorstellung in #raid-addon (RaidMasterBot/raid_addon_intro.md)",
}


def announce_series(fn: str):
    """Reihe und Version einer Ankündigung oder ihres Anhangs – (None, None) ohne Versionsnummer."""
    stem = fn[:-3] if fn.lower().endswith(".md") else fn
    if "__" not in stem:
        return None, None
    m = ANNOUNCE_VER.match(stem)
    if not m or "__" not in m.group("series"):
        return None, None
    return m.group("series").lower(), tuple(int(x) for x in m.group("ver").split("."))


def fassung(fn: str):
    """(Reihe, Fassung) jeder Ankündigung mit Kanalnamen ("__"); (None, None) für alte Dateien ohne Kanalnamen."""
    series, ver = announce_series(fn)
    if series:
        return series, ver
    if not fn.lower().endswith(".md"):
        return None, None
    stem = fn[:-3]
    if "__" not in stem:
        return None, None
    m = FASSUNG_NR.match(stem)
    if m and "__" in m.group("series"):
        return m.group("series").lower(), (int(m.group("n")),)
    return stem.lower(), (1,)


def neueste(fns) -> dict:
    """{Reihe: (Datei, Fassung)} – je Reihe die neueste Fassung."""
    out: dict = {}
    for fn in fns:
        s, v = fassung(fn)
        if s and (s not in out or v > out[s][1]):
            out[s] = (fn, v)
    return out


def aeltere(fns) -> dict:
    """{Datei: neueste Datei ihrer Reihe} für alle Dateien, die nicht die neueste Fassung ihrer Reihe sind."""
    fns = list(fns)
    top = neueste(fns)
    out = {}
    for fn in fns:
        s, v = fassung(fn)
        if s and top[s][0] != fn:
            out[fn] = top[s][0]
    return out


def split_parts(text: str, limit: int = PART_MAX) -> list[str]:
    """An Absätzen in Teile <= limit; ein längerer Absatz an Zeilen, eine einzelne zu lange Zeile hart. Nichts geht verloren."""
    pieces = []
    for para in text.split("\n\n"):
        if len(para) <= limit:
            pieces.append(para)
            continue
        cur = ""
        for ln in para.split("\n"):
            while len(ln) > limit:
                if cur:
                    pieces.append(cur)
                    cur = ""
                pieces.append(ln[:limit])
                ln = ln[limit:]
            if cur and len(cur) + 1 + len(ln) > limit:
                pieces.append(cur)
                cur = ""
            cur = (cur + "\n" + ln) if cur else ln
        if cur:
            pieces.append(cur)
    parts, cur = [], ""
    for p in pieces:
        if cur and len(cur) + len(p) + 2 > limit:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n\n" + p) if cur else p
    if cur:
        parts.append(cur)
    return parts


def old_split(text: str) -> list[str]:
    """Teilung bis Bot 1.5.193 (nur an Absätzen) – um abgeschnittene Beiträge zu erkennen (ein Teil > 2000 Zeichen)."""
    parts, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > PART_MAX and cur:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n\n" + para) if cur else para
    if cur:
        parts.append(cur)
    return parts
