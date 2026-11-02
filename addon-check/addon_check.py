#!/usr/bin/env python3
"""Prüft Addon-ZIPs von GoldSentinel, BEVOR sie veröffentlicht werden.

Warum: Im November 2026 wurden mehrere Addons mit eigenen, untereinander unverträglichen Fassungen der gemeinsamen
Datei GoldSentinelGame.lua veröffentlicht (eine davon auf CurseForge). Dieses Skript verhindert solche Fehler:

  FEHLER (Veröffentlichung wird gestoppt)
  - gemeinsame Datei GoldSentinelGame.lua weicht von shared/GoldSentinelGame.lua ab (oder wird nachgebaut)
  - gemeinsame Datei GoldSentinelDev.lua: Kopie mit gleicher Version, aber anderem Inhalt
  - Versionsnummer nicht höher als eine schon veröffentlichte (Discord-ZIPs, CurseForge) bzw. ZIP-Name passt nicht
  - .toc-Dateien eines Addons mit unterschiedlicher Version; in der .toc genannte Datei fehlt in der ZIP
  - Lua-Syntaxfehler (geprüft mit Lua 5.1 wie im Spiel)
  - GoldSentinelGame.lua steht in der .toc nicht vor den eigenen Dateien des Addons

  WARNUNG (Veröffentlichung geht, aber bitte prüfen)
  - bekannte Fallen der modernen API (Forever/Retail): alte Funktion ohne Ersatz, z. B. UnitAura ohne C_UnitAuras
  - .lua-Datei liegt im Addon, steht aber in keiner .toc; Interface 16001 (WoW Forever) fehlt
  - GoldSentinelGame.lua fehlt im Addon; GoldSentinelDev.lua veraltet (eine andere Kopie hat eine höhere Version)

Aufruf:
  python3 addon-check/addon_check.py                 alle ZIPs in download/ prüfen
  python3 addon-check/addon_check.py a.zip b.zip     nur diese ZIPs
  python3 addon-check/addon_check.py --report r.md   zusätzlich Bericht als Markdown schreiben
Rückgabe: 0 = keine Fehler, 1 = mindestens ein Fehler.
Als Modul (z. B. aus curseforge/upload.py): check_zip(path) -> Liste von Befunden (level, text).

Neue Fallen ergänzen: Liste TRAPS unten. Neue gemeinsame Datei: Liste SHARED unten.
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD = ROOT / "download"
ANNOUNCE = ROOT / "announce"
SHARED_DIR = ROOT / "shared"
UPLOADED = ROOT / "curseforge" / "uploaded.json"

# Gemeinsame Dateien: Name -> Regel
#   "exact"   : jede Kopie muss Byte für Byte der Vorlage in shared/ entsprechen
#   "version" : Kopien mit gleicher VERSION müssen gleich sein; ältere Kopien nur Warnung
SHARED = {
    "GoldSentinelGame.lua": "exact",
    "GoldSentinelDev.lua": "version",
}
# Wer GoldSentinelGame selbst nachbaut (statt die Datei zu kopieren), schreibt das hier:
REIMPL = re.compile(r"_G\.GoldSentinelGame\s*=|^\s*GoldSentinelGame\s*=", re.M)

# Bekannte Fallen der modernen API. Jede Regel: Muster im Code, Ersatz, der in DERSELBEN Datei vorkommen muss
# (sonst Warnung), und eine kurze Erklärung. Kommentarzeilen werden vorher entfernt.
TRAPS = [
    (r"\bUnitAura\s*\(", r"C_UnitAuras", "UnitAura fehlt im modernen Client -> C_UnitAuras (sonst liefert die Funktion still nichts)"),
    (r"\bUnitBuff\s*\(|\bUnitDebuff\s*\(", r"C_UnitAuras", "UnitBuff/UnitDebuff fehlen im modernen Client -> C_UnitAuras"),
    (r"\bGetSpellInfo\s*\(", r"C_Spell", "GetSpellInfo fehlt im modernen Client -> C_Spell.GetSpellInfo/GetSpellName"),
    (r"\bGetSpellCooldown\s*\(", r"C_Spell", "GetSpellCooldown fehlt im modernen Client -> C_Spell.GetSpellCooldown"),
    (r"\bGetContainer(?:NumSlots|ItemInfo|ItemLink|ItemID)\s*\(", r"C_Container", "GetContainer* fehlt im modernen Client -> C_Container"),
    (r"\bGetMerchantNumItems\b", r"C_MerchantFrame", "GetMerchantNumItems ohne C_MerchantFrame.GetNumItems als Ersatz"),
    (r"\bGetMerchantItemInfo\b", r"C_MerchantFrame", "GetMerchantItemInfo ohne C_MerchantFrame.GetItemInfo als Ersatz"),
    (r"\bGetAddOnMetadata\s*\(|\bIsAddOnLoaded\s*\(", r"C_AddOns", "GetAddOnMetadata/IsAddOnLoaded fehlen im modernen Client -> C_AddOns"),
    (r"\bInterfaceOptions_AddCategory\b", r"Settings", "InterfaceOptions_AddCategory fehlt im modernen Client -> Settings-API"),
    (r"\bEasyMenu\s*\(", r"MenuUtil|Settings", "EasyMenu fehlt im modernen Client"),
    (r"\bGetNumTradeSkills\s*\(|\bGetTradeSkillInfo\s*\(", r"C_TradeSkillUI", "alte Berufe-API ohne C_TradeSkillUI (Berufsfenster bleibt in Forever leer)"),
    (r"\bGetQuestLogTitle\s*\(", r"C_QuestLog", "GetQuestLogTitle fehlt im modernen Client -> C_QuestLog"),
    (r"\bGetPlayerMapPosition\s*\(", r"C_Map", "GetPlayerMapPosition fehlt im modernen Client -> C_Map.GetPlayerMapPosition"),
    (r"RegisterEvent[^\n]*COMBAT_LOG_EVENT_UNFILTERED|\bOn\(\s*[\"']COMBAT_LOG_EVENT_UNFILTERED",
     r"IsModern|IsOldAPI|isModern|restricted|[Cc]ombatLog\b|hasCombatLog|< *16000",
     "Kampflog wird ohne erkennbare Sperre registriert – in Forever/Retail für Addons zu, nur für die alte API registrieren"),
    (r"\bissecretvalue\s*\(", r"GoldSentinelGame|function\s+\w*[Ii]s[Ss]ecret", "issecretvalue direkt benutzt -> GoldSentinelGame.IsSecret (sicher, auch wenn die Funktion fehlt)"),
]

GAME_TESTS = SHARED_DIR / "tests" / "test_goldsentinelgame.py"


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------
def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")) or (0,)


def version_key(addon, v):
    """AHSentinel (früher AH Analyzer Pro): 5.9.x wurde zu 0.59.x – alte Nummern umrechnen (wie curseforge/upload.py)."""
    t = vtuple(v)
    if addon.lower() in ("ahanalyzerpro", "ahsentinel") and t and t[0] >= 1:
        return (0, t[0] * 10 + (t[1] if len(t) > 1 else 0)) + t[2:]
    return t


def norm(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(norm(data)).hexdigest()[:12]


def lua_version_const(text):
    m = re.search(r"^\s*local\s+VERSION\s*=\s*(\d+)", text, re.M)
    return int(m.group(1)) if m else None


def strip_lua_comments(text):
    text = re.sub(r"--\[(=*)\[.*?\]\1\]", "", text, flags=re.S)
    return re.sub(r"--[^\n]*", "", text)


def zip_name_version(path: Path):
    """download/<Addon>-<Version>.zip oder announce/<kanal>__<reihe>-<Version>.<Addon>.zip -> (Addon, Version)"""
    m = re.match(r"^[^_]+__.+?-(\d+(?:\.\d+)+)\.([A-Za-z0-9_]+)$", path.stem)
    if m:
        return m.group(2), m.group(1)
    m = re.match(r"^(.+?)-(\d+(?:\.\d+)*)$", path.stem)
    return (m.group(1), m.group(2)) if m else (path.stem, None)


_LUA = None


def lua_syntax_error(src: str, name: str):
    """Lua 5.1 (wie im Spiel). Rückgabe: Fehlertext oder None. Ohne lupa: None (Prüfung übersprungen)."""
    global _LUA
    if _LUA is None:
        try:
            import lupa.lua51 as lupa51
            rt = lupa51.LuaRuntime(unpack_returned_tuples=True)
            _LUA = rt.eval("function(s, n) local f, e = loadstring(s, n) return e end")
        except Exception:
            _LUA = False
    if not _LUA:
        return None
    err = _LUA(src, "@" + name)
    return str(err) if err else None


# ---------------------------------------------------------------------------
# bekannte veröffentlichte Versionen (Discord-ZIPs in der Git-Geschichte, CurseForge)
# ---------------------------------------------------------------------------
_PUBLISHED = None


def published_versions():
    global _PUBLISHED
    if _PUBLISHED is not None:
        return _PUBLISHED
    pub = {}

    def add(addon, ver, where):
        if ver:
            pub.setdefault(addon.lower(), {}).setdefault(ver, set()).add(where)

    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--all", "--name-only", "--format="],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        out = ""
    for line in out.splitlines():
        base = line.strip().rsplit("/", 1)[-1]
        if not base.endswith(".zip"):
            continue
        if line.startswith("download/"):
            addon, ver = zip_name_version(Path(base))
            add(addon, ver, "download/ (Git-Geschichte)")
        elif line.startswith("announce/") and "__" in base:
            # announce/<kanal>__<reihe>-<version>.<Addon>.zip
            m = re.match(r"^[^_]+__.+?-(\d+(?:\.\d+)+)\.([A-Za-z0-9_]+)\.zip$", base)
            if m:
                add(m.group(2), m.group(1), "Discord (announce/)")
    try:
        for addon, vers in json.loads(UPLOADED.read_text(encoding="utf-8")).items():
            for v in vers:
                add(addon, v, "CurseForge")
    except (OSError, ValueError):
        pass
    _PUBLISHED = pub
    return pub


# ---------------------------------------------------------------------------
# Prüfung einer ZIP
# ---------------------------------------------------------------------------
# Offizielle ältere Fassungen der "exact"-Dateien (shared/tests/variants/<Name ohne .lua>-v<N>.lua):
# eine Kopie davon ist kein Nachbau, sondern nur veraltet -> Warnung statt Fehler
def official_old(name):
    out = {}
    stem = name[:-4]
    for p in (SHARED_DIR / "tests" / "variants").glob(f"{stem}-v*.lua"):
        m = re.search(r"-v(\d+)\.lua$", p.name)
        if m:
            out[sha(p.read_bytes())] = int(m.group(1))
    return out


def load_shared():
    ref = {}
    for name in SHARED:
        p = SHARED_DIR / name
        if p.exists():
            data = p.read_bytes()
            ref[name] = {"sha": sha(data), "version": lua_version_const(data.decode("utf-8", "replace")),
                         "old": official_old(name)}
    return ref


def parse_toc(text):
    meta, files = {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^##\s*([^:]+):\s*(.*)$", line)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
        elif not line.startswith("#"):
            files.append(line.replace("\\", "/"))
    return meta, files


def check_zip(path, shared_ref=None, dev_max=None):
    """Prüft eine Addon-ZIP. Rückgabe: Liste (level, text) mit level 'FEHLER' | 'WARNUNG' | 'OK'."""
    path = Path(path)
    shared_ref = shared_ref if shared_ref is not None else load_shared()
    res = []
    err = lambda t: res.append(("FEHLER", t))
    warn = lambda t: res.append(("WARNUNG", t))

    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return [("FEHLER", "keine gültige ZIP-Datei")]
    names = [n for n in z.namelist() if not n.endswith("/")]
    lower = {n.lower(): n for n in names}
    tocs = [n for n in names if n.lower().endswith(".toc")]
    if not tocs:
        return [("FEHLER", "keine .toc in der ZIP")]

    zaddon, zver = zip_name_version(path)
    from_announce = "__" in path.stem
    folders = sorted({n.split("/", 1)[0] for n in tocs if "/" in n})
    main_versions = set()
    loaded = set()                      # Dateien, die das Spiel lädt (in einer .toc oder über eine geladene .xml)

    for folder in folders:
        ftocs = [n for n in tocs if n.startswith(folder + "/") and n.count("/") == 1]
        listed, versions, interfaces = set(), {}, set()
        for t in ftocs:
            meta, files = parse_toc(z.read(t).decode("utf-8", "replace"))
            versions[t] = meta.get("Version", "")
            interfaces.update(int(x) for x in re.findall(r"\d+", meta.get("Interface", "")))
            for f in files:
                full = f"{folder}/{f}"
                listed.add(full.lower())
                loaded.add(full.lower())
                if full.lower() not in lower:
                    err(f"{t}: Datei {f} steht in der .toc, fehlt aber in der ZIP (Lua-Fehler beim Laden)")
            # Reihenfolge: GoldSentinelGame.lua vor allen eigenen Dateien
            own = [f for f in files if f.rsplit("/", 1)[-1] not in SHARED]
            if "GoldSentinelGame.lua" in files and own:
                if files.index("GoldSentinelGame.lua") > files.index(own[0]):
                    err(f"{t}: GoldSentinelGame.lua muss vor den eigenen Dateien stehen (vor {own[0]})")
        vs = {v for v in versions.values() if v}
        if len(vs) > 1:
            err(f"{folder}: .toc-Dateien mit unterschiedlicher Version: " +
                ", ".join(f"{k.split('/')[-1]}={v}" for k, v in sorted(versions.items())))
        if folder.lower() == zaddon.lower():
            main_versions |= vs
        if 16001 not in interfaces and not any(16000 <= i <= 19999 for i in interfaces):
            warn(f"{folder}: keine Interface-Nummer für WoW Forever (16001) in der .toc")
    # .xml-Dateien, die geladen werden, laden ihrerseits <Script file="…"/> und <Include file="…"/>
    todo = [n for n in names if n.lower() in loaded and n.lower().endswith(".xml")]
    while todo:
        x = todo.pop()
        base_dir = x.rsplit("/", 1)[0]
        for f in re.findall(r'file\s*=\s*"([^"]+)"', z.read(x).decode("utf-8", "replace")):
            full = f"{base_dir}/{f.replace(chr(92), '/')}".lower()
            if full not in loaded:
                loaded.add(full)
                if full.endswith(".xml") and full in lower:
                    todo.append(lower[full])
    for n in names:
        if n.lower().endswith(".lua") and "/" in n and n.lower() not in loaded:
            warn(f"{n}: liegt im Addon, wird aber nicht geladen (in keiner .toc/.xml) – gehört nicht in die ZIP?")

    # Version: ZIP-Name, .toc, schon veröffentlicht
    if zver and main_versions and zver not in main_versions and not from_announce:
        err(f"ZIP-Name sagt {zver}, die .toc sagt {', '.join(sorted(main_versions))}")
    if from_announce:
        ver = zver if zver in main_versions else None     # Discord-Anhang eines anderen Addons: nicht vergleichen
    else:
        ver = zver or (sorted(main_versions)[0] if main_versions else None)
    if ver:
        known = published_versions().get(zaddon.lower(), {})
        higher = sorted((v for v in known if version_key(zaddon, v) > version_key(zaddon, ver)),
                        key=lambda v: version_key(zaddon, v))
        if higher:
            top = higher[-1]
            err(f"Version {ver} ist NIEDRIGER als schon veröffentlichte {top} ({', '.join(sorted(known[top]))}). "
                f"Neue Version muss höher sein als {top}, sonst bekommen Spieler das Update nicht.")

    # gemeinsame Dateien
    has_game = False
    for n in names:
        base = n.rsplit("/", 1)[-1]
        data = z.read(n)
        if base in SHARED:
            rule = SHARED[base]
            ref = shared_ref.get(base)
            v = lua_version_const(data.decode("utf-8", "replace"))
            if base == "GoldSentinelGame.lua":
                has_game = True
            if rule == "exact":
                if not ref:
                    warn(f"{n}: Vorlage shared/{base} fehlt im Repo – Vergleich übersprungen")
                elif sha(data) in ref.get("old", {}):
                    warn(f"{n}: veraltete offizielle Fassung (Version {ref['old'][sha(data)]}) – "
                         f"auf shared/{base} Version {ref['version']} aktualisieren")
                elif sha(data) != ref["sha"]:
                    err(f"{n}: weicht von shared/{base} ab (Version {v}, Vorlage Version {ref['version']}). "
                        f"Gemeinsame Datei nie selbst ändern – die Vorlage unverändert kopieren.")
            elif rule == "version" and dev_max and base in dev_max:
                top_v, top_sha = dev_max[base]
                if v is not None and v == top_v and sha(data) != top_sha:
                    err(f"{n}: gleiche Version {v} wie eine andere Kopie, aber anderer Inhalt")
                elif v is not None and v < top_v:
                    warn(f"{n}: veraltet (Version {v}, eine andere Kopie hat {top_v})")
        elif n.lower().endswith(".lua"):
            text = data.decode("utf-8", "replace")
            if REIMPL.search(text):
                err(f"{n}: baut GoldSentinelGame selbst nach – stattdessen shared/GoldSentinelGame.lua kopieren")
            e = lua_syntax_error(text, n)
            if e:
                if n.lower() in loaded:
                    err(f"Lua-Syntaxfehler: {e}")
                else:
                    warn(f"Lua-Syntaxfehler in einer Datei, die das Spiel nicht lädt (Werkzeug?): {e} – "
                         f"am besten nicht in die ZIP packen")
            code = strip_lua_comments(text)
            for pat, fallback, why in TRAPS:
                if re.search(pat, code) and not re.search(fallback, code):
                    line = next((i + 1 for i, l in enumerate(text.splitlines()) if re.search(pat, l)
                                 and not l.lstrip().startswith("--")), "?")
                    warn(f"{n}:{line}: {why}")
    if not has_game and any(f.lower() != "raidmasteruploader" for f in folders):
        warn("GoldSentinelGame.lua fehlt (gemeinsame Versionserkennung noch nicht eingebaut)")
    if not any(l == "FEHLER" for l, _ in res):
        res.insert(0, ("OK", "keine Fehler"))
    return res


def dev_versions(zips):
    """Höchste Version je 'version'-Datei über alle ZIPs: {name: (version, sha)}."""
    best = {}
    for p in zips:
        try:
            z = zipfile.ZipFile(p)
        except zipfile.BadZipFile:
            continue
        for n in z.namelist():
            base = n.rsplit("/", 1)[-1]
            if SHARED.get(base) == "version":
                data = z.read(n)
                v = lua_version_const(data.decode("utf-8", "replace"))
                if v is not None and (base not in best or v > best[base][0]):
                    best[base] = (v, sha(data))
    return best


def default_zips():
    """Alle ZIPs in download/ plus die neueste Discord-ZIP je Addon, das nicht in download/ liegt (z. B. LevelPilot)."""
    out, have = [], set()
    for p in sorted(DOWNLOAD.glob("*.zip")):
        if p.stem.endswith("-latest") or p.stem.lower().startswith("raidmasteruploader"):
            continue
        out.append(p)
        have.add(zip_name_version(p)[0].lower())
    newest = {}
    for p in ANNOUNCE.glob("*__*.zip"):
        addon, ver = zip_name_version(p)
        if not ver or addon.lower() in have:
            continue
        if addon not in newest or version_key(addon, ver) > version_key(addon, newest[addon][0]):
            newest[addon] = (ver, p)
    out += [p for _, p in sorted(newest.values(), key=lambda x: x[1].name)]
    return out


def run_game_tests():
    if not GAME_TESTS.exists():
        return None
    r = subprocess.run([sys.executable, "-I", str(GAME_TESTS)], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] if (r.stdout or r.stderr) else []


def main(argv):
    report = None
    if "--report" in argv:
        i = argv.index("--report")
        report = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    zips = [Path(a) for a in argv if not a.startswith("--")] or default_zips()
    shared_ref = load_shared()
    dev_max = dev_versions(default_zips() + zips)
    lines, failed = ["# Addon-Prüfung", ""], False

    if "GoldSentinelGame.lua" in shared_ref:
        lines.append(f"Vorlage shared/GoldSentinelGame.lua: Version {shared_ref['GoldSentinelGame.lua']['version']}")
    t = run_game_tests()
    if t is not None:
        code, tail = t
        lines.append(f"Tests der gemeinsamen Datei: {'bestanden' if code == 0 else 'FEHLGESCHLAGEN'} {' '.join(tail)}")
        failed |= code != 0
    lines.append("")

    for p in zips:
        res = check_zip(p, shared_ref, dev_max)
        bad = any(l == "FEHLER" for l, _ in res)
        failed |= bad
        n_warn = sum(1 for l, _ in res if l == "WARNUNG")
        lines.append(f"## {p.name}: {'FEHLER' if bad else 'OK'}" + (f" ({n_warn} Warnungen)" if n_warn else ""))
        for level, text in res:
            if level != "OK":
                lines.append(f"- **{level}** {text}")
        lines.append("")
    text = "\n".join(lines)
    print(text)
    if report:
        report.write_text(text + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
