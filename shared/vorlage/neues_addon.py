#!/usr/bin/env python3
"""Neues GoldSentinel-Addon aus der Vorlage erstellen.

Aufruf (im raidmaster-Repo):
    python3 shared/vorlage/neues_addon.py LootSentinel --slash ls \\
        --en "Loot helper for raids" --de "Loot-Helfer für Raids" \\
        [--farbe 3fc7eb] [--icon "Interface\\Icons\\INV_Misc_Bag_10"] [--kategorie Inventory] \\
        [--ziel <Ordner>] [--zip]

Ergebnis: <ziel>/<Name>/ mit allen Dateien der Vorlage, Platzhaltern ersetzt und den gemeinsamen Dateien
(GoldSentinelGame.lua, GoldSentinelTest.lua) unverändert aus shared/. Mit --zip zusätzlich <ziel>/<Name>-0.1.0.zip
im Aufbau wie download/ (ein Ordner <Name> in der ZIP).

Danach immer: python3 addon-check/addon_check.py <ziel>/<Name>-0.1.0.zip  -> kein FEHLER.
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "__ADDON__"
SHARED = HERE.parent
ROOT = SHARED.parent
COMMON = ["GoldSentinelGame.lua", "GoldSentinelTest.lua"]
TEXT_SUFFIXES = {".lua", ".toc", ".md", ".txt", ".xml"}
LEFTOVER = re.compile(r"__[A-Z][A-Z_]*__")


def fail(msg):
    print("FEHLER:", msg, file=sys.stderr)
    sys.exit(1)


def published_names():
    names = set()
    for d in (ROOT / "download", ROOT / "announce"):
        if d.is_dir():
            for f in d.glob("*.zip"):
                m = re.match(r"^([A-Za-z][A-Za-z0-9]*)-", f.name) or re.search(r"\.([A-Za-z0-9]+)\.zip$", f.name)
                if m:
                    names.add(m.group(1).lower())
    return names


def build(args):
    name, slash = args.name, args.slash.lower()
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]{2,40}", name):
        fail("Name: mit Grossbuchstaben beginnen, nur Buchstaben und Ziffern (z. B. LootSentinel)")
    if not re.fullmatch(r"[a-z][a-z0-9]{1,15}", slash):
        fail("--slash: 2–16 Kleinbuchstaben/Ziffern, ohne / (z. B. ls)")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", args.farbe):
        fail("--farbe: 6-stellige Hex-Farbe ohne # (z. B. 3fc7eb)")
    for label, text in (("--en", args.en), ("--de", args.de)):
        if not text.strip() or "\n" in text:
            fail(f"{label}: eine Zeile Beschreibung angeben")
    if name.lower() in published_names() and not args.force:
        fail(f"{name} ist schon veröffentlicht (download/ oder announce/). Anderen Namen wählen.")

    ziel = Path(args.ziel).resolve()
    out = ziel / name
    if out.exists():
        fail(f"{out} gibt es schon")

    repl = [   # längere Platzhalter zuerst
        ("__BESCHREIBUNG_EN__", args.en.strip()),
        ("__BESCHREIBUNG_DE__", args.de.strip()),
        ("__SLASH_GROSS__", re.sub(r"[^A-Z0-9]", "", (name + slash).upper())),
        ("__ADDON_KLEIN__", name.lower()),
        ("__KATEGORIE__", args.kategorie),
        ("__FARBE__", args.farbe.lower()),
        ("__SLASH__", slash),
        ("__ICON__", args.icon),
        ("__ADDON__", name),
    ]

    out.mkdir(parents=True)
    for src in sorted(TEMPLATE.rglob("*")):
        rel = src.relative_to(TEMPLATE)
        dst = out / Path(str(rel).replace("__ADDON__", name))
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in TEXT_SUFFIXES:
            text = src.read_text(encoding="utf-8")
            for k, v in repl:
                text = text.replace(k, v)
            left = sorted(set(LEFTOVER.findall(text)))
            if left:
                shutil.rmtree(out)
                fail(f"{rel}: Platzhalter nicht ersetzt: {', '.join(left)}")
            dst.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
    for f in COMMON:
        shutil.copy2(SHARED / f, out / f)
    print(f"Addon erstellt: {out}")

    if args.zip:
        zp = ziel / f"{name}-0.1.0.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob("*")):
                if f.is_file():
                    z.write(f, f"{name}/{f.relative_to(out).as_posix()}")
        print(f"ZIP erstellt:   {zp}")
        print(f"Jetzt prüfen:   python3 addon-check/addon_check.py {zp}")
        return out, zp
    return out, None


def main(argv=None):
    p = argparse.ArgumentParser(description="Neues GoldSentinel-Addon aus der Vorlage erstellen")
    p.add_argument("name", help="Addon-Name, z. B. LootSentinel")
    p.add_argument("--slash", required=True, help="Befehl ohne /, z. B. ls")
    p.add_argument("--en", required=True, help="Beschreibung Englisch (eine Zeile, für die .toc)")
    p.add_argument("--de", required=True, help="Beschreibung Deutsch (eine Zeile, für die .toc)")
    p.add_argument("--farbe", default="ffb238", help="Farbe des Titels, Hex ohne # (Standard: GoldSentinel-Gold)")
    p.add_argument("--icon", default="Interface\\Icons\\INV_Misc_QuestionMark", help="Symbol in der Addon-Liste")
    p.add_argument("--kategorie", default="Miscellaneous", help="X-Category in der .toc")
    p.add_argument("--ziel", default=".", help="Ordner, in dem das Addon angelegt wird (Standard: aktueller Ordner)")
    p.add_argument("--zip", action="store_true", help="zusätzlich die ZIP im Aufbau von download/ bauen")
    p.add_argument("--force", action="store_true", help="auch wenn der Name schon veröffentlicht ist (nur für Tests)")
    build(p.parse_args(argv))


if __name__ == "__main__":
    main()
