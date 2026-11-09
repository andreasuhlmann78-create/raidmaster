"""Prüfprogramm für die Wegdaten von LevelPilot (GSWEGE1).

Liest testberichte/wege/<Addon>/*.json (abgelegt von testberichte.py) und schreibt testberichte/wege/auswertung.md:
  - Ausreisser: Punkte ausserhalb der Karte, Sprünge zwischen zwei Punkten eines Wegstücks (Flug, Teleport, Messfehler)
  - Lücken: Wegnetz einer Zone zerfällt in getrennte Teile (keine bekannte Verbindung dazwischen)
  - Widersprüche: gesperrte Wegstücke, die gleichzeitig oft gelaufen werden
  - Ziele: korrigierte NPC-Orte (alt -> neu, Abstand), NPCs "nicht da"
Koordinaten sind Prozent der Zonenkarte (0–100). Läuft mit: python3 -I addon-check/wege_check.py
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEGE = ROOT / "testberichte" / "wege"

JUMP = 4.0        # Sprung zwischen zwei Punkten eines Wegstücks in Kartenprozent -> Ausreisser
SNAP = 0.6        # Punkte näher als das gelten als derselbe Knoten (Kartenprozent)
NPC_FAR = 3.0     # NPC-Korrektur grösser als das -> Datenpaket-Koordinate deutlich falsch
CONFLICT_N = 3    # gesperrt, aber so oft gelaufen -> Widerspruch


def load(base=WEGE):
    data = []
    if base.exists():
        for f in sorted(base.glob("*/*.json")):
            try:
                data.append(json.loads(f.read_text(encoding="utf-8")))
            except ValueError:
                pass
    return data


def pts(p):
    """[x1, y1, x2, y2, …] -> [(x1, y1), …]"""
    if not isinstance(p, list):
        return []
    nums = [v for v in p if isinstance(v, (int, float))]
    return list(zip(nums[0::2], nums[1::2]))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def key(pt):
    return (round(pt[0] / SNAP), round(pt[1] / SNAP))


def analyse(exports):
    zones = defaultdict(lambda: {"name": "", "edges": [], "blocked": []})
    npcs = []
    for e in exports:
        for z in e.get("zones") or []:
            m = z.get("map")
            if m is None:
                continue
            zones[m]["name"] = z.get("name") or zones[m]["name"]
            for ed in z.get("edges") or []:
                zones[m]["edges"].append({"p": pts(ed.get("p")), "src": ed.get("src"), "n": ed.get("n") or 1})
        for b in e.get("blocked") or []:
            if b.get("map") is not None:
                zones[b["map"]]["blocked"].append({"p": pts(b.get("p")), "why": b.get("why"), "t": b.get("t")})
        for n in e.get("npc") or []:
            npcs.append(n)

    report = {}
    for m, z in zones.items():
        outliers, nodes = [], {}
        parent = {}

        def find(k):
            while parent.setdefault(k, k) != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        def union(a, b):
            parent[find(a)] = find(b)

        for i, ed in enumerate(z["edges"]):
            p = ed["p"]
            for j, pt in enumerate(p):
                if not (0 <= pt[0] <= 100 and 0 <= pt[1] <= 100):
                    outliers.append(f"Wegstück {i + 1}, Punkt {j + 1}: {pt[0]:.1f},{pt[1]:.1f} ausserhalb der Karte")
            for a, b in zip(p, p[1:]):
                d = dist(a, b)
                if d > JUMP:
                    outliers.append(f"Wegstück {i + 1}: Sprung {d:.1f} % von {a[0]:.1f},{a[1]:.1f} nach {b[0]:.1f},{b[1]:.1f}")
                    continue
                union(key(a), key(b))
            for pt in p:
                nodes[key(pt)] = pt
        comps = defaultdict(list)
        for k, pt in nodes.items():
            comps[find(k)].append(pt)
        parts = sorted(comps.values(), key=len, reverse=True)
        conflicts = []
        for b in z["blocked"]:
            if not b["p"]:
                continue
            bk = {key(pt) for pt in b["p"]}
            used = sum(ed["n"] for ed in z["edges"] if bk & {key(pt) for pt in ed["p"]})
            if used >= CONFLICT_N:
                conflicts.append(f"gesperrt ({b['why']}) bei {b['p'][0][0]:.1f},{b['p'][0][1]:.1f}, aber {used}× gelaufen")
        report[m] = {"name": z["name"], "edges": len(z["edges"]), "nodes": len(nodes), "parts": parts,
                     "outliers": outliers, "blocked": z["blocked"], "conflicts": conflicts}

    npc_rows = []
    for n in npcs:
        old, new = n.get("old"), n.get("new")
        # LevelPilot schreibt "old" als [Karte, x, y], "new" als [x, y] – Karte vorne entfernen
        other_map = None
        if isinstance(old, list) and len(old) == 3:
            if old[0] != n.get("map"):
                other_map = old[0]
            old = old[1:]
        if isinstance(new, list) and len(new) == 3 and new[0] == n.get("map"):
            new = new[1:]
        o, w = pts(old), pts(new)
        if other_map is not None and w:
            npc_rows.append((n.get("id"), n.get("map"), f"Karte {other_map} -> {n.get('map')} {w[0][0]:.1f},{w[0][1]:.1f}",
                             "-", "andere Karte (Datenpaket falsch)"))
        elif o and w:
            d = dist(o[0], w[0])
            npc_rows.append((n.get("id"), n.get("map"), f"{o[0][0]:.1f},{o[0][1]:.1f} -> {w[0][0]:.1f},{w[0][1]:.1f}",
                             f"{d:.1f} %", "deutlich falsch" if d > NPC_FAR else "klein"))
        elif w and (n.get("nopack") or not o):
            # kein Ort im Datenpaket (z. B. neue Forever-NPCs): gemessener Ort ist neu, kein "nicht da"
            npc_rows.append((n.get("id"), n.get("map"), f"kein Ort im Datenpaket -> {w[0][0]:.1f},{w[0][1]:.1f}",
                             "-", "fehlt im Datenpaket"))
        else:
            npc_rows.append((n.get("id"), n.get("map"), "nicht da (Nutzer)", "-", "Ziel ausblenden"))
    return report, npc_rows


def write(report, npc_rows, out=WEGE / "auswertung.md"):
    md = ["# Auswertung der Wegdaten (GSWEGE1)", "",
          "Erzeugt von addon-check/wege_check.py. Koordinaten in Prozent der Zonenkarte.", ""]
    if not report and not npc_rows:
        md.append("Noch keine Wegdaten.")
    for m, r in sorted(report.items(), key=lambda x: str(x[0])):
        md += [f"## {r['name'] or 'Zone'} ({m})", "",
               f"- Wegstücke {r['edges']}, Knoten {r['nodes']}, zusammenhängende Teile {len(r['parts'])}"]
        if len(r["parts"]) > 1:
            md.append("- **Lücken:** das Netz zerfällt in getrennte Teile (Verbindung fehlt):")
            for i, part in enumerate(r["parts"][:8], 1):
                xs, ys = [p[0] for p in part], [p[1] for p in part]
                md.append(f"  - Teil {i}: {len(part)} Knoten, Bereich {min(xs):.0f}–{max(xs):.0f} / {min(ys):.0f}–{max(ys):.0f}")
        for o in r["outliers"][:20]:
            md.append(f"- **Ausreisser:** {o}")
        for c in r["conflicts"]:
            md.append(f"- **Widerspruch:** {c}")
        if r["blocked"]:
            md.append(f"- Gesperrte Wegstücke: {len(r['blocked'])}")
        md.append("")
    if npc_rows:
        md += ["## Korrigierte Ziele (NPC-Orte)", "", "| NPC | Karte | Ort | Abstand | Bewertung |", "|---|---|---|---|---|"]
        md += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in npc_rows]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return out


def main():
    rep, npc = analyse(load())
    p = write(rep, npc)
    issues = sum(len(r["outliers"]) + len(r["conflicts"]) + (len(r["parts"]) > 1) for r in rep.values())
    print(f"Wegdaten: {len(rep)} Zonen, {issues} Auffälligkeiten -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
