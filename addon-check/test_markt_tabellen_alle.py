"""Test: Teil "alle" der Markt-Tabellen aus den Tages-Zusammenfassungen der Sammelstelle (Masterplan AHSentinel E,
Bot D-KERN1). Nur erfundene Daten. Aufruf: python3 -I addon-check/test_markt_tabellen_alle.py"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "marktanalyse"))
import markt_tabellen as mt  # noqa: E402
from lupa.lua51 import LuaRuntime  # noqa: E402

ok = fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", name)


FEL = ["scans", "quellen", "preis_median", "preis_min", "preis_max", "menge_median", "absatz_min_tag", "absatz_max_tag"]


def day(d, tag, fr):
    (d / f"{tag}.json").write_text(json.dumps({"format": "GSMARKTT1", "tag": tag, "zone": "Europe/Zurich",
                                                "von": 1000, "bis": 2000, "felder": FEL, "fraktionen": fr}),
                                    encoding="utf-8")


with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    check("leerer Ordner -> kein Teil", mt.alle(d) is None)
    check("fehlender Ordner -> kein Teil", mt.alle(d / "gibtsnicht") is None)
    # Tag 1: H, vergleich 10 h; Item 2589 Preis 100, Absatz 2..4; Item 2592 ohne Preis
    day(d, "2026-11-14", {"H": {"vergleich_h": 10, "items": {
        "2589": [5, 2, 100, 90, 120, 40, 2, 4], "2592": [3, 1, None, None, None, None, 1, 1]}}})
    # Tag 2: H, vergleich 30 h; Item 2589 Preis 140, Absatz 6..8; A: Item 2589 Preis 300
    day(d, "2026-11-15", {"H": {"vergleich_h": 30, "items": {"2589": [7, 3, 140, 130, 150, 30, 6, 8]}},
                          "A": {"vergleich_h": 5, "items": {"2589": [1, 1, 300, 300, 300, 2, None, None]}}})
    (d / "kaputt.json").write_text("{nicht json", encoding="utf-8")
    (d / "fremd.json").write_text(json.dumps({"format": "ANDERS"}), encoding="utf-8")
    a = mt.alle(d)
    h = a["H"][2589]
    check("Tage gezählt (nur gültige Dateien)", a["tage"] == 2)
    check("Felder benannt", a["felder"] == ["preis", "absatzMin", "absatzMax", "quellen", "tage", "scans"])
    check("Preis = Median der Tages-Mediane (100,140 -> 120)", h[0] == 120)
    # Summe/Summe: (2*10 + 6*30) / 40 = 5.0 ; (4*10 + 8*30) / 40 = 7.0
    check("Absatz Untergrenze Summe/Summe gewichtet = 5.0", h[1] == 5.0)
    check("Absatz Obergrenze Summe/Summe gewichtet = 7.0", h[2] == 7.0)
    check("Quellen = höchste Tageszahl 3", h[3] == 3)
    check("Tage 2, Scans 12", h[4] == 2 and h[5] == 12)
    check("Item ohne Preis fehlt", 2592 not in a["H"])
    check("Fraktion A getrennt, Absatz unbekannt -> nil", a["A"][2589][0] == 300 and a["A"][2589][1] is None)
    # Lua: Zahl-Schlüssel, ladbar, keine Namen
    text = "GoldSentinelMarktTabellen = " + mt.lua_val({"v": 1, "alle": a})
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(text)
    T = lua.globals().GoldSentinelMarktTabellen
    check("in Lua mit Zahl nachschlagbar", T.alle.H[2589][1] == 120 and T.alle.H[2589][2] == 5.0)
    check("Zahl-Schlüssel, kein Text-Schlüssel", "[2589]" in text and '["2589"]' not in text)
    check("nil-Absatz als nil", T.alle.A[2589][2] is None)
    # Grösse: viele Items -> wird gekürzt, Anzahl steht drin, die mit den meisten Scans bleiben
    many = {str(10000 + i): [1 + (i % 50), 2, 1000 + i, 1, 1, 1, 0.5, 1.5] for i in range(4000)}
    day(d, "2026-11-16", {"H": {"vergleich_h": 24, "items": many}})
    b = mt.alle(d, max_bytes=20 * 1024)
    size = len(mt.lua_val(b))
    check(f"auf Grenze gekürzt ({size} <= 20480)", size <= 20 * 1024)
    check("weggelassen gezählt", b["weggelassen"] > 0 and b["weggelassen"] + len(b["H"]) + len(b.get("A", {})) == 4002)
    kept = [v[5] for v in b["H"].values()]
    dropped_max = max(1 + (i % 50) for i in range(4000) if (10000 + i) not in b["H"])
    check("behalten werden die Items mit den meisten Scans", min(kept) >= dropped_max)
    check("2589 (12 Scans) bleibt bei Kürzung nur nach Scans", (2589 in b["H"]) == (12 >= dropped_max))
    # nur die neuesten keep Tage
    c = mt.alle(d, keep=1)
    check("keep=1 -> nur neuester Tag", c["tage"] == 1 and 2589 not in c.get("H", {}))

print(f"{ok}/{ok + fail} Prüfungen bestanden")
sys.exit(1 if fail else 0)
