"""Auswertung und Abgleich MARKT-KERN <-> Prüf-Sitzung (Entscheid des Nutzers 16.11.2026 04:51/04:52: "du und der Kern tauschen
Daten aus und gleichen ab – du wertest das Ganze aus"; Ziel: der Kern arbeitet möglichst wirkungsvoll, hat alle Daten und kommt
bald in P2).

Aufruf:  python3 -I kern_abgleich.py <AHSentinel.lua> [weitere ...] [--tabelle GoldSentinelMarktTabellen.lua] [--aus bericht.md]
Liest die Zähler des Kerns (AHSentinelDB.kern) und die Journale (forecast.list) und schreibt einen Bericht (Markdown):
  1. Stand je Weg: Fälle, Bewertung (30 Tage), Status wie im Addon (K:Show nachgebildet) und was bis P2 fehlt.
  2. Abgleich Verkauf: Kern-Zellen "sell" gegen den Tabellen-Teil "verkauf" (dieselben Fälle, zwei Zählweisen -> müssen
     innerhalb der Unsicherheit übereinstimmen; sonst Zählfehler auf einer Seite).
  3. Abgleich Kaufen: Kern "buyk"/"buye" (Σ Kaufpreis / Σ Erlös je Stufe) gegen den Teil "kaufen".
  4. Was die Prüf-Sitzung dem Kern zurückgibt (Teil "kern" der Markt-Tabellen).
Nur Zahlen, keine Namen.
"""
import sys
import datetime
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markt_tabellen as mt  # noqa: E402
import kern_daten as kd  # noqa: E402

ORDER = ["markt", "sell", "gilde", "marktu", "buyk", "buye", "buyp", "buyr"]


def fmt_day(d):
    return datetime.datetime.fromtimestamp(d, mt.Z).strftime("%d.%m.") if d else "-"


def bericht(dbs, labels):
    out = []
    now = datetime.datetime.now(mt.Z).strftime("%d.%m.%Y %H:%M")
    out.append(f"# MARKT-KERN – Auswertung und Abgleich ({now})")
    out.append("")
    out.append("Erstellt von der Prüf-Sitzung mit `addon-check/marktanalyse/kern_abgleich.py`. Regeln wie Kern.lua (L4-Gewicht, P2, P4).")
    out.append("")
    J = mt.merge_journals(dbs)                              # Journal aller Stände ohne Doppelte (wie die Tabelle)
    newest = kd.newest_stores(dbs)
    kds = []
    for db, lab in zip(dbs, labels):
        if not any(db is x for x in newest):
            continue
        k = kd.kern_of(db)
        if not k:
            out.append(f"- {lab}: keine Kern-Daten")
            continue
        kds.append((k, db, lab))
    for k, db, lab in kds:
        today = kd.newest_day(k)
        out.append(f"## Daten {lab} (neuester Tag {fmt_day(today)})")
        out.append("")
        out.append("### 1. Stand je Weg")
        out.append("")
        out.append("| Weg | Zellen | Fälle (gewichtet) | bewertet n | Brier neu | Brier Grundlinie | Treffer neu − Grundlinie | Tage mit Bewertung | Addon (K:Show) | Prüf-Sitzung |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
        ways = sorted(set(k["c"]) | set(k["e"]), key=lambda w: (ORDER.index(w) if w in ORDER else 99, w))
        for w in ways:
            cells = k["c"].get(w, {})
            nf = sum(kd.counts(k, w, z, today)[0] for z in cells)
            if w in k["e"]:
                first = None
                try:
                    first = db.kern.first and db.kern.first[w]
                except Exception:
                    first = None
                ok, why, r = kd.show(k, w, today, first)
                u_ok, u_why = kd.useful(k, w, today)
                n = r["n"]
                out.append(f"| {w} | {len(cells)} | {nf:.0f} | {n:.0f} | {r['bN'] / n:.4f} | {r['bB'] / n:.4f} | {r['hN'] - r['hB']:+.0f} | "
                           f"{len(k['e'][w])} | {'P2' if ok else why} | {u_why} |")
            else:
                out.append(f"| {w} | {len(cells)} | {nf:.0f} | – | – | – | – | – | (nur Zähler) | – |")
        out.append("")
        # Abgleich Verkauf
        out.append("### 2. Abgleich Verkauf: Kern \"sell\" gegen Tabelle \"verkauf\" (gleiche Fälle)")
        out.append("")
        tab = mt.sell_quotes([J])
        out.append("| Zelle | Kern n | Kern Quote | Tabelle n | Tabelle Quote | 95 %-Bereich Kern | Befund |")
        out.append("|---|---:|---:|---:|---:|---|---|")
        bands = mt.PRICE_BANDS
        bad = 0
        for z in sorted(k["c"].get("sell", {})):
            if z.startswith("g:"):
                continue
            g, cls = z.rsplit(":", 1)
            n, y = kd.counts(k, "sell", z, today)
            row = None
            try:
                b = bands[int(cls) - 1]
                row = next((r for r in tab.get(g, []) if r["bis"] == b), None)
            except (ValueError, IndexError):
                pass
            lo, hi = kd.wilson(y, n)
            if row:
                ok = lo - 1e-9 <= row["quote"] <= hi + 1e-9
                bad += 0 if ok else 1
                out.append(f"| {z} | {n:.0f} | {y / n:.3f} | {row['n']} | {row['quote']:.3f} | {lo:.3f}–{hi:.3f} | {'passt' if ok else 'WEICHT AB'} |")
            else:
                out.append(f"| {z} | {n:.0f} | {y / n if n else 0:.3f} | – | – | {lo:.3f}–{hi:.3f} | Tabelle hat die Zelle nicht |")
        out.append("")
        out.append(f"Abweichungen ausserhalb des 95 %-Bereichs: {bad}.")
        out.append("")
        # harte Prüfung: jeder abgeschlossene Verkaufsfall seit dem Start des Kerns muss genau einmal im Kern stehen
        filled = db.kern.filled or 0
        if filled:
            fd = kd.day_start(filled)
            jn, jy = collections.Counter(), collections.Counter()
            L = J.forecast.list
            for i in range(1, len(L) + 1):
                e = mt.decode(L[i], mt.P_F) if L[i] and L[i][0] == "P" else None
                if not e or e["r"] in ("", "u", "c"):
                    continue
                stop = mt.BASE + int(e["t"]) * 60 + int(float(e["d"] or 24)) * 3600
                if stop < filled:
                    continue
                rel = mt.num(e["rel"]) or 1
                cell = f'{e["g"] or "misc"}:{next(i for i, x in enumerate(mt.PRICE_BANDS, 1) if rel <= x)}'
                jn[cell] += 1
                jy[cell] += max(0.0, min(1.0, (mt.num(e["sq"]) or 0) / max(1.0, mt.num(e["q"]) or 1)))
            kn, ky = collections.Counter(), collections.Counter()
            for z, days in k["c"].get("sell", {}).items():
                if z.startswith("g:"):
                    continue
                for d, (a, b) in days.items():
                    if d >= fd:
                        kn[z] += a
                        ky[z] += b
            out.append(f"Harte Prüfung seit Kern-Start ({fmt_day(filled)}): jeder abgeschlossene Verkaufsfall muss genau einmal im Kern stehen.")
            out.append("")
            out.append("| Zelle | Journal Fälle | davon verkauft (Summe Anteil) | Kern Fälle | Kern verkauft | Befund |")
            out.append("|---|---:|---:|---:|---:|---|")
            miss = 0
            for z in sorted(set(jn) | set(kn)):
                same = abs(jn[z] - kn[z]) < 0.5 and abs(jy[z] - ky[z]) < 0.05
                miss += 0 if same else 1
                out.append(f"| {z} | {jn[z]} | {jy[z]:.2f} | {kn[z]:.0f} | {ky[z]:.2f} | {'geht auf' if same else 'FEHLT IM KERN' if kn[z] < jn[z] else 'WEICHT AB'} |")
            out.append("")
            out.append(f"Zellen, die nicht aufgehen: {miss} (Ziel 0). Hinweis: Fälle am Rand (Tagesgrenze des Kern-Starts) können um 1 abweichen.")
            out.append("")
        # Abgleich Kaufen
        out.append("### 3. Abgleich Kaufen: Kern \"buyk\"/\"buye\" gegen Tabelle \"kaufen\"")
        out.append("")
        kt = mt.buy_bands([J])
        out.append("| Stufe (Kaufpreis/Wert) | Kern Käufe | Kern Gewinn Σ/Σ | Tabelle n | Tabelle Gewinn | Differenz |")
        out.append("|---|---:|---:|---:|---:|---:|")
        for i, b in enumerate(mt.BUY_BANDS, 1):
            n, sk = kd.counts(k, "buyk", f"b{i}", today)
            _, se = kd.counts(k, "buye", f"b{i}", today)
            g = (se / sk - 1) if sk > 0 else None
            row = next((r for r in kt if r.get("bis") == b), None)
            tg = row["gewinn"] if row else None
            diff = f"{(g - tg) * 100:+.1f} Pkt." if g is not None and tg is not None else "–"
            out.append(f"| ≤ {'∞' if b >= 99 else b} | {n:.0f} | {('%+.1f %%' % (g * 100)) if g is not None else '–'} | "
                       f"{row['n'] if row else '–'} | {('%+.1f %%' % (tg * 100)) if tg is not None else '–'} | {diff} |")
        out.append("")
        out.append("Hinweis: Die Tabelle zählt alle Käufe aller Stände (zusammengeführt, ohne Doppelte), der Kern nur die letzten 30 Tage "
                   "mit Gewicht (≤ 14 Tage 1, sonst 0,5) – kleine Differenzen sind daher erwartet; grosse = Zählfehler suchen.")
        out.append("")
    part, info = kd.kern_teil([db for _, db, _ in kds])
    out.append("## 4. Rückgabe an den Kern (Teil \"kern\" der Markt-Tabellen)")
    out.append("")
    out.append(f"Quellen mit Kern-Daten: {info['quellen']}. Wege: " + (", ".join(f"{w}: {why}" for w, why in info["wege"].items()) or "keine"))
    out.append("")
    if part:
        for w, cells in part.items():
            out.append(f"- {w}: {len(cells)} Zellen (n ≥ {kd.KERN_MIN_N}): " + ", ".join(f"{z} {v['p']:.3f} (n {v['n']})" for z, v in cells.items()))
    else:
        out.append("- nichts weitergegeben")
    out.append("")
    return "\n".join(out), part, info


def main(argv):
    args = argv[1:]
    aus = None
    if "--aus" in args:
        i = args.index("--aus")
        aus = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 1
    dbs = [mt.load(p) for p in args]
    labels = [Path(p).parent.parent.parent.name + "/" + Path(p).parent.parent.name if len(Path(p).parts) > 3 else p for p in args]
    text, _, _ = bericht(dbs, labels)
    if aus:
        Path(aus).parent.mkdir(parents=True, exist_ok=True)
        Path(aus).write_text(text + "\n", encoding="utf-8")
        print("geschrieben:", aus)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
