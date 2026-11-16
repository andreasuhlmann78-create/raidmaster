"""Auswertung einer GSWegMess-Messung (Supervisor, 16.11.2026).

Aufruf:  python3 -I shared/messtest/GSWegMess/auswerten.py <SavedVariables/GSWegMess.lua>

Liest GSWegMessDB.lines (Spalten: Zeit|x|y|Karte|Kleinkarte|Zone|Unterzone|Minikarte|drinnen|fällt|schwimmt|Tempo|Ereignis/Notiz)
und beantwortet die Frage des Konzepts (shared/wissen/analysen/levelpilot-wegfuehrung-3d.md Abschnitt 6):
"Welches Zeichen trennt welche Ebene?"
Ausgabe:
  1. Abschnitte zwischen zwei Notizen (MARK) mit Dauer und den Werten jedes Zeichens darin.
  2. Je Zeichen (Karte, Kleinkarte, Unterzone, Minikarte, drinnen) die Wechsel und ob ein Wechsel ohne 2D-Bewegung vorkam
     (Hinweis auf Aufzug/Treppe = Ebenenwechsel) – und Stellen, an denen sich in 2D nahe Punkte (≤ 10 Yards in Prozent grob)
     in diesem Zeichen unterscheiden (= es trennt Ebenen, die 2D nicht trennt).
  3. Ereignisse ZONE_CHANGED* / NEW_WMO_CHUNK und Stürze (fällt = 1).
Nur Zahlen/Texte aus der Datei, keine Namen von Spielern (die Datei enthält keine).
"""
import re
import sys
from collections import Counter, defaultdict

COLS = ["t", "x", "y", "map", "sub", "zone", "subzone", "mini", "indoors", "falling", "swimming", "speed", "ev"]
SIGNALS = ["map", "sub", "subzone", "mini", "indoors"]


def read_lines(text):
    """Die Einträge aus GSWegMessDB.lines (Lua-Zeichenketten) lesen – ohne Lua, nur die Liste."""
    m = re.search(r'\["lines"\]\s*=\s*\{(.*?)\n\s*\}', text, re.S)
    if not m:
        return []
    out = []
    for s in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)):
        out.append(s.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
                   if "\\" in s else s)
    return out


def parse(lines):
    rows = []
    for ln in lines:
        if ln.startswith("#"):
            continue
        p = ln.split("|")
        if len(p) < len(COLS):
            continue
        r = dict(zip(COLS, p[:len(COLS) - 1] + ["|".join(p[len(COLS) - 1:])]))
        try:
            r["t"] = float(r["t"])
        except ValueError:
            continue
        for k in ("x", "y", "speed"):
            try:
                r[k] = float(r[k])
            except ValueError:
                r[k] = None
        rows.append(r)
    return rows


def sections(rows):
    secs, cur = [], {"name": "(Start)", "rows": []}
    for r in rows:
        ev = r["ev"] or ""
        if ev.startswith("MARK"):
            secs.append(cur)
            cur = {"name": ev[4:].strip() or "(Notiz)", "rows": [r]}
        else:
            cur["rows"].append(r)
    secs.append(cur)
    return [s for s in secs if s["rows"]]


def near(a, b, lim=0.15):
    """grob: zwei Punkte derselben Karte liegen in 2D nahe (Prozent der Karte, 0,15 % ~ 5–15 Yards in Städten)"""
    if a["map"] != b["map"] or None in (a["x"], a["y"], b["x"], b["y"]):
        return False
    return abs(a["x"] - b["x"]) <= lim and abs(a["y"] - b["y"]) <= lim


def analyse(rows):
    rep = []
    secs = sections(rows)
    rep.append(f"Zeilen: {len(rows)} · Abschnitte: {len(secs)}")
    rep.append("")
    rep.append("1. ABSCHNITTE (zwischen den Notizen)")
    for s in secs:
        rr = s["rows"]
        dur = rr[-1]["t"] - rr[0]["t"]
        vals = {k: sorted({r[k] for r in rr}) for k in SIGNALS}
        rep.append(f"- {s['name']}: {dur:.0f} s, {len(rr)} Zeilen")
        for k in SIGNALS:
            rep.append(f"    {k}: {' / '.join(vals[k])}")
    rep.append("")
    rep.append("2. ZEICHEN – WECHSEL UND TRENNKRAFT")
    for k in SIGNALS:
        changes, still, sep = 0, 0, 0
        for a, b in zip(rows, rows[1:]):
            if a[k] != b[k]:
                changes += 1
                if near(a, b, 0.05):
                    still += 1
        # Paare naher Punkte (auch zeitlich weit auseinander), die sich nur in diesem Zeichen unterscheiden
        seen = set()
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a[k] != b[k] and near(a, b):
                    key = (a[k], b[k]) if a[k] < b[k] else (b[k], a[k])
                    seen.add(key)
        sep = len(seen)
        rep.append(f"- {k}: {changes} Wechsel, davon {still} fast ohne 2D-Bewegung · trennt {sep} Ebenen-Paar(e) an derselben 2D-Stelle"
                   + ("" if not seen else ": " + "; ".join(f"{x} ≠ {y}" for x, y in sorted(seen)[:6])))
    rep.append("")
    rep.append("3. EREIGNISSE UND STÜRZE")
    evc = Counter((r["ev"] or "").split(" ")[0] for r in rows if r["ev"] and not r["ev"].startswith("MARK"))
    rep.append("- Ereignisse: " + (", ".join(f"{k} {v}" for k, v in sorted(evc.items())) or "keine"))
    falls = sum(1 for a, b in zip(rows, rows[1:]) if a["falling"] != "1" and b["falling"] == "1")
    rep.append(f"- Stürze (fällt 0 -> 1): {falls}")
    rep.append("")
    rep.append("FOLGERUNG (automatisch, vom Supervisor zu prüfen): Ein Zeichen taugt als Ebenen-Schlüssel, wenn es an derselben 2D-Stelle")
    rep.append("verschiedene Werte zeigt (Spalte 'trennt') und auf einer Ebene stabil bleibt (wenig Wechsel ohne Bewegung ausser an Toren).")
    return "\n".join(rep)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 1
    text = open(argv[1], encoding="utf-8", errors="replace").read()
    rows = parse(read_lines(text))
    if not rows:
        print("Keine Messzeilen gefunden (GSWegMessDB.lines leer oder Datei unbekannt).")
        return 2
    print(analyse(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
