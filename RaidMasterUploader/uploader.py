"""
RaidMaster-Uploader – läuft auf dem PC, auf dem WoW gespielt wird.

Sobald WoW die Datei RaidMaster.lua speichert (nach /reload oder beim Ausloggen), wird sie gepackt
und über einen geheimen Discord-Webhook in den Kanal #bot-daten geschickt. Der Bot auf dem Server
liest sie dort und aktualisiert DKP, Loot, Einteilung und Skillungen.

Start: uploader.bat (Doppelklick). Einrichtung: in Discord /uploader ausführen und die Datei
uploader_config.json in diesen Ordner legen. Nur Python 3 nötig, keine weiteren Pakete.

Erstkill-Screenshots (ab 1.6.0): RaidMaster macht beim Erstkill einen Screenshot und merkt sich die Zeit
(RaidMasterDB.shotList). Der Uploader sucht im Screenshots-Ordner von WoW das passende Bild und schickt es
beim nächsten Upload mit. Andere Screenshots werden nie hochgeladen.

Ab 1.7.0:
- Sucht bei jedem Start und danach alle paar Minuten nach einer neueren RaidMaster.lua (z. B. nach dem Wechsel vom
  Anniversary- in den Forever-Client) und wechselt mit Meldung im Fenster dorthin.
- Gildenbank auch von GuildSentinel: GuildSentinel.lua aus demselben SavedVariables-Ordner geht als zweiter Anhang mit,
  wenn sie sich geändert hat und einen Gildenbank-Bestand enthält (["bank"]). Sonst wird sie nie geschickt.
  Pfad überschreiben: "guildsentinel_path" in uploader_config.json.

Ab 1.8.0 – Testberichte der GoldSentinel-Addons (#testberichte):
- Durchsucht alle *.lua im SavedVariables-Ordner nach Berichten ("GSTEST1…", geschrieben von GoldSentinelTest in
  RaidMaster, ThreatSentinel, BuffSentinel …) und schickt neue gesammelt an den zweiten Webhook "test_webhook_url"
  (Kanal #testberichte, liest die Addon-Prüfung). Nur diese Berichte, sonst nichts aus fremden SavedVariables.
- Unabhängig vom Daten-Upload: ein Fehler beim einen verhindert das andere nie.
- Fehlt test_webhook_url (ältere uploader_config.json): einmal Hinweis "/uploader erneut ausführen", sonst wie bisher.

Ab 1.9.0 – Diagnose-Protokolle und Wegdaten (gleicher Weg, gleicher Kanal #testberichte):
- "GSDIAG1|…"-Diagnoseprotokolle (z. B. AHSentinelDB.diagExport, ProfessionSentinelDB.diagExport) und
  "GSWEGE1{…}"-Wegdaten (LevelPilotDB.wegeExport) aus den SavedVariables nach /reload oder Ausloggen mitschicken.
- Nur diese Zeichenketten, genau so wie sie in den SavedVariables stehen (Anhang gsextras.lua.gz), nichts sonst.
- Nur wenn neu: gemerkt wird ein Prüfwert des Inhalts (sent_extra_ids, höchstens 500). Grössenregeln wie bei
  den Testberichten (je Nachricht höchstens 4 MB entpackt, einzelne über 512 KB werden übersprungen).

Ab 2.0.0 – nur noch Neues, ein Paket, höchstens alle 15 Minuten (Entscheid des Nutzers, 9. Nov. 2026):
- Testberichte je Kennung nur einmal, Diagnose-Protokolle nur mit neuen Einträgen, Wegdaten je Inhalt einmal,
  gleiche Fehler nur einmal ganz und danach nur als Zähler.
- Alles Neue in EINER Nachricht mit EINEM Anhang paket-<Zeit>.json.gz ({"items": [...]}).
- Änderungen werden gesammelt; ein Paket höchstens alle 15 Minuten, der Rest beim Beenden.
- Gemerkter Stand in uploader_state.json (uploader_config.json bleibt unverändert).
"""

from __future__ import annotations

import glob
import gzip
import json
import os
import re
import socket
import string
import sys
import time
import urllib.error
import urllib.request
import uuid

VERSION = "2.0.1"
SHOT_WINDOW = (-30, 180)          # Bild darf so viele Sekunden vor/nach der gemerkten Zeit entstanden sein
SHOT_MAX_BYTES = 9 * 1024 * 1024
SHOT_MAX_AGE = 14 * 86400
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "uploader_config.json")
USER_AGENT = f"RaidMasterUploader (https://github.com, {VERSION})"
RESCAN_SECONDS = 300              # so oft nach einer neueren RaidMaster.lua suchen (Wechsel in den Forever-Ordner)
NEWER_BY_SECONDS = 60             # erst wechseln, wenn die gefundene Datei so viel neuer ist
GS_BANK = re.compile(rb'\["bank"\]\s*=\s*\{')

# Testberichte (GoldSentinelTest): gleiche Regeln wie addon-check/testberichte.py (Gegenstelle der Addon-Prüfung)
TEST_PREFIX = "GSTEST1"
TEST_STR = re.compile(r'"(' + TEST_PREFIX + r'(?:[^"\\]|\\.)*)"', re.S)
TEST_MAX_JSON = 4 * 1024 * 1024        # entpackt höchstens so viel je Nachricht
TEST_MAX_SENT_IDS = 500
TEST_USERNAME = "GoldSentinel-Testberichte"
TEST_STABLE_SECONDS = 2
EXTRA_PREFIXES = ("GSDIAG1", "GSWEGE1")
EXTRA_STR = re.compile(r'"((?:GSDIAG1\||GSWEGE1\{)(?:[^"\\]|\\.)*)"', re.S)
EXTRA_MAX_ONE = 512 * 1024              # so wertet die Addon-Prüfung höchstens aus (testberichte.MAX_EXTRA)
EXTRA_MAX_SENT_IDS = 500


def log(msg: str):
    print(time.strftime("%H:%M:%S") + "  " + msg, flush=True)


def load_config() -> dict:
    if not os.path.isfile(CONFIG):
        log("uploader_config.json fehlt. In Discord /uploader ausführen und die Datei in diesen Ordner legen:")
        log("  " + HERE)
        input("Enter zum Beenden ...")
        sys.exit(1)
    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("webhook_url", "").startswith("https://"):
        log("In uploader_config.json fehlt der Webhook-Link – /uploader in Discord erneut ausführen.")
        input("Enter zum Beenden ...")
        sys.exit(1)
    return cfg


def save_config(cfg: dict):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def find_saved_variables() -> list[str]:
    """Sucht RaidMaster.lua in typischen WoW-Ordnern auf allen Laufwerken."""
    pattern_tail = os.path.join("WTF", "Account", "*", "SavedVariables", "RaidMaster.lua")
    roots = []
    if os.name == "nt":
        roots = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        roots = [os.path.expanduser("~")]
    found = set()
    for root in roots:
        for depth in range(0, 4):
            middle = [root] + ["*"] * depth
            for path in glob.glob(os.path.join(*middle, pattern_tail)):
                found.add(os.path.normpath(path))
    return sorted(found, key=lambda p: os.path.getmtime(p), reverse=True)


def choose_path(cfg: dict) -> str:
    path = cfg.get("savedvariables_path") or ""
    if path and os.path.isfile(path):
        return path
    log("Suche die RaidMaster-Datei von WoW ... (kann eine Minute dauern)")
    found = find_saved_variables()
    if not found:
        log("Nicht gefunden. Bitte in uploader_config.json bei \"savedvariables_path\" den Pfad eintragen, z. B.")
        log('  "C:/Games/WoW Forever/WTF/Account/ANDI/SavedVariables/RaidMaster.lua"')
        log("Die Datei entsteht erst, wenn RaidMaster installiert ist und du einmal eingeloggt warst.")
        input("Enter zum Beenden ...")
        sys.exit(1)
    if len(found) > 1:
        log("Mehrere gefunden – nehme die zuletzt geänderte:")
        for p in found:
            log("  " + p)
    path = found[0].replace("\\", "/")
    cfg["savedvariables_path"] = path
    save_config(cfg)
    return path


def newer_saved_variables(path: str, found: list[str] | None = None) -> str | None:
    """Gibt es eine deutlich neuere RaidMaster.lua als die überwachte (z. B. im Forever-Ordner)? Dann ihr Pfad."""
    if found is None:
        found = find_saved_variables()
    try:
        current = os.path.getmtime(path) if path and os.path.isfile(path) else 0
    except OSError:
        current = 0
    for cand in found:
        if os.path.normpath(cand) == os.path.normpath(path or ""):
            continue
        try:
            if os.path.getmtime(cand) > current + NEWER_BY_SECONDS:
                return cand.replace("\\", "/")
        except OSError:
            pass
        break                                   # found ist nach Datum sortiert: nur die neueste zählt
    return None


def switch_if_newer(cfg: dict, path: str, found: list[str] | None = None) -> str:
    new = newer_saved_variables(path, found)
    if not new:
        return path
    log("Neuere RaidMaster-Datei gefunden (z. B. nach dem Wechsel in einen anderen WoW-Client).")
    log("Wechsle zu: " + new)
    cfg["savedvariables_path"] = new
    save_config(cfg)
    return new


def guildsentinel_path(cfg: dict, path: str) -> str:
    """GuildSentinel.lua liegt im selben SavedVariables-Ordner wie RaidMaster.lua."""
    return cfg.get("guildsentinel_path") or os.path.join(os.path.dirname(os.path.abspath(path)), "GuildSentinel.lua")


def read_guildsentinel(gs_path: str) -> bytes | None:
    """GuildSentinel.lua nur mit Gildenbank-Bestand – sonst nichts schicken (keine fremden Daten)."""
    try:
        with open(gs_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    return raw if GS_BANK.search(raw) else None


def build_body(payload: dict, packed: bytes, gs_packed: bytes | None, shots: list[tuple[str, str, bytes]]) -> tuple[str, bytes]:
    """Multipart-Inhalt: files[0] = RaidMaster.lua.gz (immer zuerst), files[1] = GuildSentinel.lua.gz (falls dabei),
    danach die Screenshots. shots = [(Name, Content-Type, Daten)]."""
    boundary = "----RaidMaster" + uuid.uuid4().hex
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
        json.dumps(payload).encode("utf-8"), b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[0]"; filename="RaidMaster.lua.gz"\r\n'
        b"Content-Type: application/gzip\r\n\r\n",
        packed, b"\r\n",
    ]
    n = 1
    if gs_packed is not None:
        parts += [f"--{boundary}\r\n".encode(),
                  b'Content-Disposition: form-data; name="files[1]"; filename="GuildSentinel.lua.gz"\r\n'
                  b"Content-Type: application/gzip\r\n\r\n",
                  gs_packed, b"\r\n"]
        n = 2
    for i, (name, ctype, data) in enumerate(shots, n):
        parts += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="files[{i}]"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode(),
                  data, b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(parts)


# ---------------------------------------------------------------------------
# Testberichte (#testberichte)
# ---------------------------------------------------------------------------
def lua_unescape(s: str) -> str:
    """Lua-String aus SavedVariables zurückwandeln (wie testberichte.lua_unescape): \\" \\\\ \\n \\t \\r,
    Backslash + Zeilenumbruch, \\ddd (Bytes, danach latin-1 -> UTF-8)."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n.isdigit():
                m = re.match(r"\d{1,3}", s[i + 1:])
                out.append(chr(int(m.group(0))))
                i += 1 + len(m.group(0))
                continue
            out.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "\n": "\n"}.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    text = "".join(out)
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def reports_in_text(text: str, source: str = "") -> list[dict]:
    """Alle GSTEST1-Berichte in einem SavedVariables-Text. Kaputte werden mit Log-Zeile übersprungen."""
    found = []
    for m in TEST_STR.finditer(text):
        raw = lua_unescape(m.group(1))[len(TEST_PREFIX):]
        try:
            rep = json.loads(raw)
        except ValueError:
            log(f"Testbericht in {source or 'Datei'} nicht lesbar – übersprungen.")
            continue
        if isinstance(rep, dict) and rep.get("id"):
            found.append(rep)
    return found


def extras_in_text(text: str) -> list[dict]:
    """GSDIAG1-/GSWEGE1-Zeichenketten in einem SavedVariables-Text, unverändert (noch Lua-escaped).
    id = Prüfwert des Inhalts, kind = "diag" oder "wege"."""
    import hashlib
    out = []
    for m in EXTRA_STR.finditer(text):
        raw = m.group(1)
        out.append({"id": "x-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16],
                    "kind": "diag" if raw.startswith("GSDIAG1") else "wege", "raw": raw})
    return out


# ---------------------------------------------------------------------------
# Ab 2.0.0: nur noch Neues, gesammelt in EINEM Paket, höchstens alle 15 Minuten
# (auftraege/RaidMaster/anweisung-uploader-nur-neues.txt, Entscheid des Nutzers 9. Nov. 2026)
# - Testberichte (GSTEST1, kind "test") je Kennung nur einmal – auch nach /reload, Relog, Neustart.
# - Fehlerberichte (GSTEST1, kind "fehler"): gleiche Fehler nur einmal ganz, danach nur der Zähler ("jetzt N×").
# - Diagnose-Protokolle (GSDIAG1): nur wenn im Abschnitt "Einträge" etwas Neues steht (Kopfzeilen und Uhrzeit der
#   Ausgabe zählen nicht).
# - Wegdaten (GSWEGE1): je Inhalt nur einmal.
# - Alles Neue in EINER Nachricht mit EINEM Anhang paket-<Zeit>.json.gz: {"items": ["GSTEST1…", "GSDIAG1|…", …]}.
# - Gemerkter Stand in uploader_state.json neben dem Uploader (nie in uploader_config.json).
# ---------------------------------------------------------------------------
STATE = os.path.join(HERE, "uploader_state.json")
SEND_EVERY = 15 * 60                    # höchstens so oft ein Paket; Änderungen so lange sammeln
STATE_MAX_IDS = 5000
DIAG_ENTRIES = re.compile(r"^== Eintr", re.M)
DIAG_TIME = re.compile(r"\d\d\.\d\d\.(?:\d{2,4})?\s*\d\d:\d\d(?::\d\d)?")


def _hash(s: str, n: int = 16) -> str:
    import hashlib
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def load_state(cfg: dict | None = None) -> dict:
    """uploader_state.json lesen. Beim ersten Start mit 2.0.0 die gemerkten Kennungen aus der alten
    uploader_config.json übernehmen (nur lesen – die Datei wird nicht verändert)."""
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            st = json.load(f)
        if isinstance(st, dict):
            st.setdefault("sent_test_ids", [])
            st.setdefault("errors", {})
            st.setdefault("diag", {})
            st.setdefault("wege", [])
            return st
    except (OSError, ValueError):
        pass
    cfg = cfg or {}
    return {"sent_test_ids": list(cfg.get("sent_test_ids") or []), "errors": {}, "diag": {},
            "wege": list(cfg.get("sent_extra_ids") or []), "last_sent": 0}


def save_state(st: dict):
    st["sent_test_ids"] = st.get("sent_test_ids", [])[-STATE_MAX_IDS:]
    st["wege"] = st.get("wege", [])[-STATE_MAX_IDS:]
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def diag_entries(text: str) -> list[str]:
    """Prüfwerte der Einträge eines Diagnose-Protokolls – ohne Kopfzeilen und ohne die Uhrzeit der Ausgabe.
    Ein neuer Eintrag oder ein gestiegener Zähler (×N) ergibt einen neuen Prüfwert."""
    m = DIAG_ENTRIES.search(text)
    if m:
        body = text[m.end():].split("\n", 1)[1] if "\n" in text[m.end():] else ""
        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    else:
        # anderes Format: alles ausser der ersten Zeile, Uhrzeiten entfernt
        lines = [DIAG_TIME.sub("", ln).strip() for ln in text.split("\n")[1:] if ln.strip()]
    return sorted({_hash(ln, 12) for ln in lines})


def error_sig(addon: str, e: dict) -> str:
    stack = "\n".join(str(e.get("stack") or "").split("\n")[:3])
    return _hash(f"{addon}|{e.get('msg')}|{e.get('wo')}|{stack}")


class Collector:
    """Liest die *.lua im SavedVariables-Ordner (nur geänderte neu) und baut daraus das Paket mit allem Neuen."""

    def __init__(self, folder: str):
        self.folder = folder
        self.mtimes: dict[str, float] = {}
        self.texts: dict[str, str] = {}

    def refresh(self, now: float | None = None, stable: bool = True) -> bool:
        """True, wenn sich eine Datei mit GSTEST1/GSDIAG1/GSWEGE1 geändert hat."""
        now = time.time() if now is None else now
        changed = False
        for fn in sorted(glob.glob(os.path.join(self.folder, "*.lua"))):
            try:
                mt = os.path.getmtime(fn)
            except OSError:
                continue
            if self.mtimes.get(fn) == mt or (stable and now - mt < TEST_STABLE_SECONDS):
                continue
            try:
                with open(fn, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            self.mtimes[fn] = mt
            if TEST_PREFIX in text or any(p in text for p in EXTRA_PREFIXES):
                if self.texts.get(fn) != text:
                    changed = True
                self.texts[fn] = text
            else:
                self.texts.pop(fn, None)
        return changed

    def build(self, st: dict) -> dict:
        """Paket aus allem Neuen gegenüber dem gemerkten Stand. Verändert st NICHT (erst nach dem Senden: commit)."""
        sent = set(st.get("sent_test_ids") or [])
        known_err = dict(st.get("errors") or {})
        known_wege = set(st.get("wege") or [])
        items, marks, rest = [], [], {"ids": []}      # je Item, was nach dem Senden gemerkt wird (ab 2.0.1 je Teil)
        new_ids, wege_ids, diag_state, err_state = [], [], {}, {}
        counts = {"test": 0, "fehler": 0, "zaehler": 0, "diag": 0, "wege": 0}
        fehler: dict[str, dict] = {}         # je Addon ein zusammengefasster Fehlerbericht
        seen = set()
        for fn in sorted(self.texts):
            text = self.texts[fn]
            for rep in reports_in_text(text, os.path.basename(fn)):
                rid = str(rep.get("id"))
                if rid in sent or rid in seen:
                    continue
                seen.add(rid)
                new_ids.append(rid)
                if rep.get("kind") != "fehler":
                    items.append(TEST_PREFIX + json.dumps(rep, ensure_ascii=False, separators=(",", ":")))
                    marks.append({"ids": [rid]})
                    counts["test"] += 1
                    continue
                addon = str(rep.get("addon") or "?")
                box = fehler.setdefault(addon, {"rep": rep, "errors": {}, "ids": []})
                box["ids"].append(rid)
                if (rep.get("time") or 0) >= (box["rep"].get("time") or 0):
                    box["rep"] = rep
                for e in rep.get("errors") or []:
                    if not isinstance(e, dict):
                        continue
                    sig = error_sig(addon, e)
                    n = int(e.get("count") or 1)
                    cur = box["errors"].get(sig)
                    if cur is None:
                        before = int(known_err.get(sig, 0))
                        entry = dict(e)
                        entry["count"] = before + n
                        if before:
                            # schon gemeldet: nur der Zähler, ohne Stapel
                            entry = {"msg": e.get("msg"), "wo": e.get("wo"), "version": e.get("version"),
                                     "count": before + n, "nur_zaehler": True, "vorher": before}
                        box["errors"][sig] = entry
                    else:
                        cur["count"] = int(cur.get("count") or 0) + n
        for addon, box in sorted(fehler.items()):
            if not box["errors"]:
                rest["ids"] += box["ids"]
                continue
            rep = dict(box["rep"])
            rep["errors"] = list(box["errors"].values())
            items.append(TEST_PREFIX + json.dumps(rep, ensure_ascii=False, separators=(",", ":")))
            mark = {"ids": list(box["ids"]), "errors": {}}
            for sig, e in box["errors"].items():
                err_state[sig] = int(e.get("count") or 0)
                mark["errors"][sig] = err_state[sig]
                counts["zaehler" if e.get("nur_zaehler") else "fehler"] += 1
            marks.append(mark)
        for fn in sorted(self.texts):
            for x in extras_in_text(self.texts[fn]):
                raw = lua_unescape(x["raw"])
                if len(raw.encode("utf-8")) > EXTRA_MAX_ONE:
                    # ab 2.0.1 nur beim ersten Mal melden (Prüfwert in uploader_state.json "zu_gross")
                    big = st.setdefault("zu_gross", [])
                    if x["id"] not in big:
                        big.append(x["id"])
                        del big[:-200]
                        log(f"{'Diagnose' if x['kind'] == 'diag' else 'Wegdaten'} zu gross – übersprungen.")
                        try:
                            save_state(st)
                        except OSError:
                            pass
                    continue
                if x["kind"] == "wege":
                    if x["id"] in known_wege or x["id"] in wege_ids:
                        continue
                    wege_ids.append(x["id"])
                    items.append(raw)
                    marks.append({"wege": [x["id"]]})
                    counts["wege"] += 1
                    continue
                parts = raw.split("|", 3)
                addon = parts[1] if len(parts) >= 4 else "?"
                entries = diag_entries(parts[3] if len(parts) >= 4 else raw)
                old = set((st.get("diag") or {}).get(addon) or []) | set(diag_state.get(addon) or [])
                if addon in diag_state or (old and set(entries) <= old):
                    continue                 # nichts Neues (oder schon im Paket)
                if not entries and addon in (st.get("diag") or {}):
                    continue
                diag_state[addon] = entries
                items.append(raw)
                marks.append({"diag": {addon: entries}})
                counts["diag"] += 1
        return {"items": items, "marks": marks, "rest": rest, "ids": new_ids, "wege": wege_ids, "diag": diag_state,
                "errors": err_state, "counts": counts}


def commit(st: dict, pkg: dict, now: float | None = None, marks: list[dict] | None = None):
    """Nach erfolgreichem Senden (oder wenn nichts zu senden war) den Stand merken.
    marks = nur diese Teile (ab 2.0.1: je gesendetem Teil eines grossen Pakets), sonst alles."""
    if marks is None:
        marks = list(pkg.get("marks") or []) + [pkg.get("rest") or {}]
        if "marks" not in pkg:          # (älterer Aufbau ohne marks)
            marks = [{"ids": pkg["ids"], "wege": pkg["wege"], "diag": pkg["diag"], "errors": pkg["errors"]}]
    known = set(st.get("sent_test_ids") or [])
    st["sent_test_ids"] = list(st.get("sent_test_ids") or [])
    st["wege"] = list(st.get("wege") or [])
    for m in marks:
        st["sent_test_ids"] += [i for i in m.get("ids") or [] if i not in known]
        known.update(m.get("ids") or [])
        st["wege"] += [w for w in m.get("wege") or [] if w not in st["wege"]]
        st.setdefault("diag", {}).update(m.get("diag") or {})
        st.setdefault("errors", {}).update(m.get("errors") or {})
    if pkg["items"]:
        st["last_sent"] = time.time() if now is None else now
    save_state(st)


def package_summary(c: dict) -> str:
    parts = []
    for key, word in (("test", "Testbericht(e)"), ("fehler", "neue(r) Fehler"), ("zaehler", "Fehler nur Zähler"),
                      ("diag", "Diagnose-Protokoll(e)"), ("wege", "Wegdaten")):
        if c.get(key):
            parts.append(f"{c[key]} {word}")
    return "GoldSentinel-Paket: " + (", ".join(parts) or "nichts Neues")


def package_bodies(pkg: dict, now: float | None = None) -> list[tuple[str, bytes]]:
    """Normalfall EINE Nachricht; nur wenn das Paket entpackt über 4 MB wäre, mehrere Teile."""
    now = time.time() if now is None else now
    chunks, cur, size = [], [], 0
    for idx, it in enumerate(pkg["items"]):
        n = len(it.encode("utf-8")) + 4
        if cur and size + n > TEST_MAX_JSON:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(idx)
        size += n
    if cur:
        chunks.append(cur)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now))
    out = []
    for i, chunk in enumerate(chunks, 1):
        name = f"paket-{stamp}.json.gz" if len(chunks) == 1 else f"paket-{stamp}-{i}.json.gz"
        content = package_summary(pkg["counts"]) + ("" if len(chunks) == 1 else f" (Teil {i}/{len(chunks)})")
        payload = {"content": content, "username": TEST_USERNAME, "allowed_mentions": {"parse": []}}
        packed = gzip.compress(json.dumps({"items": [pkg["items"][i] for i in chunk]}, ensure_ascii=False)
                               .encode("utf-8"), 9)
        boundary = "----GSPaket" + uuid.uuid4().hex
        body = b"".join([
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n',
            json.dumps(payload).encode("utf-8"), b"\r\n",
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="files[0]"; filename="{name}"\r\n'.encode(),
            b"Content-Type: application/gzip\r\n\r\n",
            packed, b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ])
        out.append((boundary, body, chunk))
    return out


def send_package(cfg: dict, st: dict, pkg: dict, sleep=time.sleep, now: float | None = None) -> str:
    """"ok" (gesendet und gemerkt), "leer" (nichts Neues, Stand trotzdem gemerkt), "invalid", "error"."""
    if not pkg["items"]:
        commit(st, pkg, now)
        return "leer"
    url = cfg.get("test_webhook_url") or ""
    if not url.startswith("https://"):
        return "invalid"
    marks = pkg.get("marks") or []
    first = True
    for boundary, body, chunk in package_bodies(pkg, now):
        result = post_webhook(url, boundary, body, sleep)
        if result != "ok":
            return result
        # ab 2.0.1: jeden gesendeten Teil sofort merken – schlägt Teil 2 fehl, kommt Teil 1 nicht nochmals
        part = [marks[i] for i in chunk if i < len(marks)]
        if first:
            part.append(pkg.get("rest") or {})
            first = False
        commit(st, pkg, now, part)
    log(package_summary(pkg["counts"]) + " – an #testberichte geschickt.")
    return "ok"


class Reporter:
    """Sammelt Änderungen und schickt höchstens alle 15 Minuten ein Paket; flush() beim Beenden."""

    def __init__(self, cfg: dict, folder: str, st: dict | None = None, sleep=time.sleep):
        self.cfg, self.sleep = cfg, sleep
        self.st = st if st is not None else load_state(cfg)
        self.collector = Collector(folder)
        self.first_pending: float | None = None
        self.failures, self.next_try = 0, 0.0

    def set_folder(self, folder: str):
        if folder != self.collector.folder:
            self.collector = Collector(folder)

    def due(self, now: float) -> bool:
        if self.first_pending is None or now < self.next_try:
            return False
        return now - self.first_pending >= SEND_EVERY and now - float(self.st.get("last_sent") or 0) >= SEND_EVERY

    def tick(self, now: float | None = None) -> str | None:
        now = time.time() if now is None else now
        if not (self.cfg.get("test_webhook_url") or "").startswith("https://"):
            return None
        if self.collector.refresh(now) and self.first_pending is None:
            if self.collector.build(self.st)["items"]:
                self.first_pending = now
                log("Neues für #testberichte gefunden – wird gesammelt und spätestens in 15 Minuten geschickt.")
        if not self.due(now):
            return None
        return self._send(now)

    def _send(self, now: float) -> str:
        pkg = self.collector.build(self.st)
        result = send_package(self.cfg, self.st, pkg, self.sleep, now)
        if result in ("ok", "leer"):
            self.first_pending, self.failures = None, 0
        else:
            self.failures += 1
            self.next_try = now + min(600, 30 * self.failures)
            log("Webhook für #testberichte ungültig – /uploader erneut ausführen." if result == "invalid"
                else "Paket für #testberichte konnte nicht geschickt werden – neuer Versuch später.")
        return result

    def flush(self, now: float | None = None) -> str | None:
        """Beim Beenden: Rest sofort senden (ohne 15-Minuten-Frist)."""
        now = time.time() if now is None else now
        if not (self.cfg.get("test_webhook_url") or "").startswith("https://"):
            return None
        self.collector.refresh(now, stable=False)
        return self._send(now)


def post_webhook(url: str, boundary: str, body: bytes, sleep=time.sleep) -> str:
    """"ok", "invalid" (401/404), "error" (5xx, Verbindung, sonst). 429 wird abgewartet und wiederholt."""
    full = url + ("&" if "?" in url else "?") + "wait=true"
    req = urllib.request.Request(full, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    wait = float(json.loads(e.read().decode()).get("retry_after", 5))
                except (ValueError, AttributeError):
                    wait = 5
                sleep(min(wait, 60) + 0.5)
                continue
            if e.code in (401, 404):
                return "invalid"
            return "error"
        except (urllib.error.URLError, OSError):
            return "error"
    return "error"



def screenshots_dir(path: str) -> str:
    """.../<WoW>/WTF/Account/<X>/SavedVariables/RaidMaster.lua -> .../<WoW>/Screenshots"""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(path))))))
    return os.path.join(root, "Screenshots")


def find_shots(cfg: dict, path: str, raw: bytes) -> list[tuple[str, str]]:
    """Erstkill-Screenshots, die noch nicht geschickt wurden: [(Dateipfad, Name im Upload)]."""
    m = re.search(rb'\["shotList"\]\s*=\s*"([0-9:;]*)"', raw)
    if not m:
        return []
    folder = cfg.get("screenshots_path") or screenshots_dir(path)
    if not os.path.isdir(folder):
        return []
    files = []
    for fn in os.listdir(folder):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            full = os.path.join(folder, fn)
            try:
                files.append((os.path.getmtime(full), full))
            except OSError:
                pass
    sent = set(cfg.get("sent_shots") or [])
    out = []
    now = time.time()
    for part in m.group(1).decode().split(";"):
        t, _, enc = part.partition(":")
        if not t.isdigit() or part in sent or now - int(t) > SHOT_MAX_AGE:
            continue
        t = int(t)
        cands = [(abs(mt - t), full) for mt, full in files if SHOT_WINDOW[0] <= mt - t <= SHOT_WINDOW[1]]
        if not cands:
            continue
        full = min(cands)[1]
        if os.path.getsize(full) > SHOT_MAX_BYTES:
            continue
        ext = os.path.splitext(full)[1].lower()
        out.append((full, f"shot_{enc}_{t}{ext}", part))
    return out


def upload(cfg: dict, path: str, gs_raw: bytes | None = None) -> bool:
    with open(path, "rb") as f:
        raw = f.read()
    packed = gzip.compress(raw, 9)
    gs_packed = gzip.compress(gs_raw, 9) if gs_raw else None
    shots = []
    try:
        # Discord nimmt pro Nachricht nur ca. 10 MB an: Bilder nur, solange alles zusammen darunter bleibt
        total = len(packed) + len(gs_packed or b"")
        for shot in find_shots(cfg, path, raw):
            size = os.path.getsize(shot[0])
            if total + size <= SHOT_MAX_BYTES:
                shots.append(shot)
                total += size
    except OSError:
        shots = []
    bot_id = str(cfg.get("bot_id") or "")
    payload = {
        "content": (f"<@{bot_id}> " if bot_id else "") + "RaidMaster-Daten",
        "username": f"RaidMaster-Uploader ({socket.gethostname()[:20]})",
        "allowed_mentions": {"parse": [], "users": [bot_id] if bot_id else []},
    }
    shot_data = []
    for full, name, _ in shots:
        with open(full, "rb") as f:
            shot_data.append((name, "image/png" if name.endswith(".png") else "image/jpeg", f.read()))
    boundary, body = build_body(payload, packed, gs_packed, shot_data)
    url = cfg["webhook_url"] + ("&" if "?" in cfg["webhook_url"] else "?") + "wait=true"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            log(f"Hochgeladen ({len(raw) // 1024} KB, gepackt {len(packed) // 1024} KB)."
                + (" Dazu der Gildenbank-Bestand aus GuildSentinel." if gs_packed else "")
                + (f" Dazu {len(shots)} Erstkill-Screenshot(s)." if shots else ""))
            if shots:
                cfg["sent_shots"] = (list(cfg.get("sent_shots") or []) + [p for _, _, p in shots])[-200:]
                save_config(cfg)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    wait = float(json.loads(e.read().decode()).get("retry_after", 5))
                except ValueError:
                    wait = 5
                time.sleep(min(wait, 60) + 0.5)
                continue
            if e.code in (401, 404):
                log("Der Webhook-Link ist ungültig (gelöscht?). In Discord /uploader erneut ausführen.")
                return False
            log(f"Discord antwortet mit Fehler {e.code}.")
            return False
        except (urllib.error.URLError, OSError) as e:
            log(f"Keine Verbindung ({e}). Neuer Versuch später.")
            return False
    return False


def gs_mtime(gs_path: str) -> float:
    try:
        return os.path.getmtime(gs_path)
    except OSError:
        return 0


_flushed = []


def _flush_on_exit(reporter: "Reporter"):
    """Beim Beenden (Fenster schliessen, Strg+C, Abmelden) den gesammelten Rest sofort schicken – einmal."""
    import atexit
    import signal

    def flush(*_):
        if _flushed:
            return
        _flushed.append(True)
        try:
            reporter.flush()
        except Exception as e:  # noqa: BLE001
            log(f"Testberichte beim Beenden: {e}")

    atexit.register(flush)
    if sys.platform == "win32":
        # Fenster schliessen (CTRL_CLOSE_EVENT): Windows gibt dem Programm ein paar Sekunden – Rest dann senden
        try:
            import ctypes
            handler_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)

            def on_console(event):
                if event in (0, 1, 2, 5, 6):        # Strg+C, Strg+Pause, Schliessen, Abmelden, Herunterfahren
                    flush()
                return 0                             # danach wie gewohnt beenden

            _flush_on_exit.handler = handler_type(on_console)   # Verweis halten
            ctypes.windll.kernel32.SetConsoleCtrlHandler(_flush_on_exit.handler, True)
        except Exception:  # noqa: BLE001
            pass
    for name in ("SIGTERM", "SIGBREAK", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, lambda *a: (flush(), sys.exit(0)))
            except (ValueError, OSError):
                pass


def main():
    log(f"RaidMaster-Uploader {VERSION}")
    cfg = load_config()
    stored = cfg.get("savedvariables_path") or ""
    had_stored = bool(stored) and os.path.isfile(stored)
    path = choose_path(cfg)
    if had_stored:
        # gespeicherter Pfad: trotzdem suchen – nach dem Forever-Start liegt die aktuelle Datei woanders
        log("Prüfe, ob es eine neuere RaidMaster-Datei gibt (z. B. im Forever-Ordner) ...")
        path = switch_if_newer(cfg, path)
    log("Überwache: " + path)
    log("Fenster offen lassen. Nach /reload oder Ausloggen werden die Daten automatisch hochgeladen.")
    interval = max(3, int(cfg.get("check_seconds") or 10))
    reporter = Reporter(cfg, os.path.dirname(os.path.abspath(path)))
    _flush_on_exit(reporter)
    if not (cfg.get("test_webhook_url") or "").startswith("https://"):
        log("Hinweis: Für Testberichte (#testberichte) in Discord /uploader erneut ausführen und die neue "
            "uploader_config.json hineinlegen. Der Daten-Upload läuft trotzdem wie bisher.")
    last_sent = 0.0
    last_gs_seen = 0.0          # zuletzt gesehene Änderung von GuildSentinel.lua
    pending_gs = None           # GuildSentinel.lua mit Bestand, die noch mitgeschickt werden muss
    failures = 0
    next_try = 0.0
    next_scan = time.time() + RESCAN_SECONDS
    while True:
        if time.time() >= next_scan:
            next_scan = time.time() + RESCAN_SECONDS
            new = switch_if_newer(cfg, path)
            if new != path:
                path = new
                last_sent = 0.0
                reporter.set_folder(os.path.dirname(os.path.abspath(path)))
                log("Überwache: " + path)
        gs_file = guildsentinel_path(cfg, path)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        gmt = gs_mtime(gs_file)
        if gmt and gmt != last_gs_seen:
            time.sleep(2)                       # warten, bis WoW fertig geschrieben hat
            if gs_mtime(gs_file) != gmt:
                continue
            last_gs_seen = gmt
            # nur mit Gildenbank-Bestand – sonst löst GuildSentinel.lua keinen Upload aus
            pending_gs = read_guildsentinel(gs_file) or pending_gs
        if mtime and (mtime != last_sent or pending_gs) and time.time() >= next_try:
            # warten, bis WoW fertig geschrieben hat
            time.sleep(2)
            try:
                if os.path.getmtime(path) != mtime:
                    continue
            except OSError:
                continue
            if upload(cfg, path, pending_gs):
                last_sent = mtime
                pending_gs = None
                failures = 0
            else:
                failures += 1
                next_try = time.time() + min(600, 30 * failures)
        # Testberichte, Diagnose, Wegdaten: eigener Weg, gesammelt, höchstens alle 15 Minuten ein Paket.
        # Fehler hier stören den Daten-Upload nie.
        try:
            reporter.tick()
        except Exception as e:  # noqa: BLE001
            log(f"Testberichte: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
