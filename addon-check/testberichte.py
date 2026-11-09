#!/usr/bin/env python3
"""Testberichte der GoldSentinel-Addons einsammeln und auswerten (Prüf-Sitzung).

Weg: Addon (shared/GoldSentinelTest.lua) -> SavedVariables -> RaidMasterUploader -> Discord #testberichte
     -> dieses Skript (GitHub-Workflow testberichte.yml) -> testberichte/ im Repo -> Prüf-Sitzung.

Aufruf:
  python3 addon-check/testberichte.py                 Discord-Kanal lesen (DISCORD_BOT_TOKEN), dann auswerten
  python3 addon-check/testberichte.py --import DATEI  Berichte aus einer Datei übernehmen: SavedVariables (*.lua),
                                                      testberichte.json(.gz) vom Uploader oder ein einzelner Bericht
  python3 addon-check/testberichte.py --nur-auswerten status.md/status.json neu schreiben

Ergebnis:
  testberichte/berichte/<Addon>/<id>.json   jeder Bericht einmal (nach id)
  testberichte/status.md                    für Menschen: je Addon letzter Testlauf, FEHLER, Fehler im Spiel
  testberichte/status.json                  maschinenlesbar, mit "offen" (alles, was die Prüf-Sitzung ansehen muss)

Die Berichte kommen von den PCs der Spieler: Sie gelten als ungeprüfte Daten. Es wird nur JSON gelesen, Grössen und
Namen werden begrenzt, nichts daraus wird ausgeführt.
"""
import datetime as dt
import gzip
import io
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "testberichte"
STORE = OUT / "berichte"
PREFIX = "GSTEST1"
CHANNEL = os.environ.get("TESTBERICHTE_KANAL", "testberichte")
API = "https://discord.com/api/v10"
HISTORY = 500
MAX_FILE = 5 * 1024 * 1024
MAX_REPORT = 512 * 1024
SAFE = re.compile(r"[^A-Za-z0-9_.\-]")
LUA_STR = re.compile(r'"(' + PREFIX + r'(?:[^"\\]|\\.)*)"', re.S)
# Weitere Kennungen (gleicher Weg wie GSTEST1):
#   GSDIAG1|<Addon>|<Version>|…|<Text>   Diagnose-Protokoll (Vorlage Diag.lua, ProfessionSentinel, AHSentinel, …)
#   GSWEGE1{JSON}                        Wegdaten von LevelPilot (kind = "wege", Felder siehe auftraege/LevelPilot)
DIAG_PREFIX, WEGE_PREFIX = "GSDIAG1", "GSWEGE1"
DIAG_OUT, WEGE_OUT = OUT / "diagnose", OUT / "wege"
LUA_EXTRA = re.compile(r'"((?:' + DIAG_PREFIX + "|" + WEGE_PREFIX + r')(?:[^"\\]|\\.)*)"', re.S)
MAX_EXTRA = 512 * 1024
# Namen schwärzen: Das Repo ist öffentlich. Spieler-/Charakternamen, die Addons versehentlich mitschicken, werden vor
# dem Speichern durch "<Name>" ersetzt. Die Liste kommt NUR aus dem GitHub-Secret REDACT_NAMES (Komma-getrennt) –
# nie Namen in diese Datei oder ins Repo schreiben.
_REDACT = sorted({n.strip() for n in os.environ.get("REDACT_NAMES", "").split(",") if len(n.strip()) >= 3},
                 key=len, reverse=True)


def redact(text):
    if not _REDACT or not isinstance(text, str):
        return text
    for n in _REDACT:
        text = re.sub(r"(?<![\wÄÖÜäöüß])" + re.escape(n) + r"(?![\wÄÖÜäöüß])", "<Name>", text)
    return text


# ---------------------------------------------------------------------------
# Berichte erkennen und prüfen
# ---------------------------------------------------------------------------
def lua_unescape(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n.isdigit():                                   # \ddd (Byte dezimal)
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
    # WoW schreibt UTF-8; \ddd-Bytes wieder zu UTF-8 zusammensetzen
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def clean(rep):
    """Bericht prüfen und auf erlaubte Felder kürzen. None = unbrauchbar."""
    if not isinstance(rep, dict) or rep.get("f") != 1 or rep.get("kind") not in ("test", "fehler"):
        return None
    addon, rid = str(rep.get("addon") or ""), str(rep.get("id") or "")
    if not addon or not rid or len(addon) > 60 or len(rid) > 120:
        return None
    rep["addon"] = SAFE.sub("_", addon)
    rep["id"] = SAFE.sub("_", rid)
    for key in ("results", "errors"):
        if key in rep and not isinstance(rep[key], list):
            rep[key] = []
    if not isinstance(rep.get("counts"), dict):
        rep["counts"] = {}
    if not isinstance(rep.get("env"), dict):
        rep["env"] = {}
    return rep


def from_text(text):
    """Alle Berichte in einem Text: GSTEST1-Strings (SavedVariables) oder JSON (Liste / einzelner Bericht)."""
    found = []
    for m in LUA_STR.finditer(text):
        raw = lua_unescape(m.group(1))[len(PREFIX):]
        try:
            found.append(json.loads(raw))
        except ValueError:
            pass
    if not found:
        t = text.strip()
        if t.startswith(PREFIX):
            t = t[len(PREFIX):]
        try:
            data = json.loads(t)
            items = data if isinstance(data, list) else [data]
            for x in items:
                if isinstance(x, str) and x.startswith(PREFIX):
                    x = json.loads(x[len(PREFIX):])
                found.append(x)
        except ValueError:
            pass
    return [r for r in (clean(x) for x in found) if r]


def from_bytes(name, data):
    if len(data) > MAX_FILE:
        return []
    if name.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            data = gzip.GzipFile(fileobj=io.BytesIO(data)).read(MAX_FILE + 1)
        except (OSError, EOFError, ValueError):
            return []
        if len(data) > MAX_FILE:
            return []
    return from_text(data.decode("utf-8", "replace"))


def extras_from_text(text):
    """GSDIAG1-Protokolle und GSWEGE1-Wegdaten in einem Text (SavedVariables oder Discord-Nachricht)."""
    diags, wege = [], []
    raws = [lua_unescape(m.group(1)) for m in LUA_EXTRA.finditer(text)]
    t = text.strip()
    if not raws and (t.startswith(DIAG_PREFIX) or t.startswith(WEGE_PREFIX)):
        raws = [t]
    for raw in raws:
        if len(raw) > MAX_EXTRA:
            continue
        if raw.startswith(DIAG_PREFIX + "|"):
            parts = raw.split("|", 3)
            if len(parts) >= 4 and parts[1] and len(parts[1]) <= 60:
                diags.append({"addon": SAFE.sub("_", parts[1]), "version": SAFE.sub("_", parts[2])[:30], "text": raw})
        elif raw.startswith(WEGE_PREFIX):
            try:
                w = json.loads(raw[len(WEGE_PREFIX):])
            except ValueError:
                continue
            if isinstance(w, dict) and w.get("kind") == "wege" and w.get("addon") and w.get("id"):
                w["addon"], w["id"] = SAFE.sub("_", str(w["addon"]))[:60], SAFE.sub("_", str(w["id"]))[:120]
                wege.append(w)
    return diags, wege


def store_extras(diags, wege):
    """Diagnose als Text (nach Inhalt einmalig), Wegdaten als JSON (nach id). Gibt (neu Diagnose, neu Wege)."""
    import hashlib
    nd = nw = 0
    for d in diags:
        h = hashlib.sha1(d["text"].encode("utf-8")).hexdigest()[:12]
        p = DIAG_OUT / d["addon"] / f"{d['version']}-{h}.txt"
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(redact(d["text"].split("|", 3)[3] if d["text"].count("|") >= 3 else d["text"]), encoding="utf-8")
            nd += 1
    for w in wege:
        p = WEGE_OUT / w["addon"] / f"{w['id']}.json"
        if not p.exists():
            body = redact(json.dumps(w, ensure_ascii=False, indent=1, sort_keys=True))
            if len(body) <= MAX_EXTRA:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body + "\n", encoding="utf-8")
                nw += 1
    return nd, nw


def store(reports):
    new = 0
    for r in reports:
        p = STORE / r["addon"] / f"{r['id']}.json"
        if p.exists():
            continue
        body = redact(json.dumps(r, ensure_ascii=False, indent=1, sort_keys=True))
        if len(body) > MAX_REPORT:
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body + "\n", encoding="utf-8")
        new += 1
    return new


# ---------------------------------------------------------------------------
# Discord lesen
# ---------------------------------------------------------------------------
def _add_extras(name, data):
    if len(data) > MAX_FILE:
        return
    if name.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            data = gzip.GzipFile(fileobj=io.BytesIO(data)).read(MAX_FILE + 1)
        except (OSError, EOFError, ValueError):
            return
    d, w = extras_from_text(data.decode("utf-8", "replace"))
    fetch_discord.extras[0].extend(d)
    fetch_discord.extras[1].extend(w)


def fetch_discord():
    import requests
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        return None, "Secret DISCORD_BOT_TOKEN fehlt (GitHub: Settings -> Secrets and variables -> Actions)."
    s = requests.Session()
    s.headers.update({"Authorization": f"Bot {token}", "User-Agent": "GoldSentinel-Testberichte (github actions)"})

    def get(path, **params):
        for _ in range(6):
            r = s.get(API + path, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.2)
                continue
            if r.status_code in (401, 403):
                raise PermissionError(f"Discord {r.status_code} bei {path}")
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Discord: zu viele Anfragen bei {path}")

    try:
        guilds = get("/users/@me/guilds")
    except PermissionError as e:
        return None, f"Discord lehnt den Token ab ({e})."
    want = os.environ.get("DISCORD_GUILD_ID", "").strip()
    guild = next((g for g in guilds if g["id"] == want), None) if want else (guilds[0] if guilds else None)
    if not guild:
        return None, "Der Bot ist auf keinem Server (oder DISCORD_GUILD_ID passt nicht)."
    chans = [c for c in get(f"/guilds/{guild['id']}/channels") if c.get("type") in (0, 5) and c.get("name") == CHANNEL]
    if not chans:
        return None, f"Kanal #{CHANNEL} gibt es (noch) nicht – der Bot legt ihn bei /uploader an."
    reports, before, seen = [], None, 0
    fetch_discord.extras = ([], [])
    try:
        while seen < HISTORY:
            params = {"limit": 100}
            if before:
                params["before"] = before
            batch = get(f"/channels/{chans[0]['id']}/messages", **params)
            if not batch:
                break
            seen += len(batch)
            before = batch[-1]["id"]
            for m in batch:
                for a in m.get("attachments", []):
                    fn = a.get("filename", "")
                    if not re.search(r"\.(json|json\.gz|lua|gz)$", fn) or a.get("size", 0) > MAX_FILE:
                        continue
                    if not str(a.get("url", "")).startswith("https://cdn.discordapp.com/"):
                        continue
                    r = s.get(a["url"], timeout=60)
                    if r.ok:
                        reports += from_bytes(fn, r.content)
                        _add_extras(fn, r.content)
                content = m.get("content", "").lstrip()
                if content.startswith(PREFIX):
                    reports += from_text(content)
                if content.startswith(DIAG_PREFIX) or content.startswith(WEGE_PREFIX):
                    _add_extras("nachricht.txt", content.encode("utf-8"))
            if len(batch) < 100:
                break
    except PermissionError:
        return None, f"Der Bot darf #{CHANNEL} nicht lesen."
    return reports, None


# ---------------------------------------------------------------------------
# Auswerten
# ---------------------------------------------------------------------------
def load_all():
    out = {}
    if not STORE.exists():
        return out
    for p in sorted(STORE.glob("*/*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out.setdefault(r.get("addon", p.parent.name), []).append(r)
    for lst in out.values():
        lst.sort(key=lambda r: (r.get("time") or 0, r.get("id")))
    return out


def ts(t):
    try:
        return dt.datetime.fromtimestamp(int(t), dt.timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    except (TypeError, ValueError, OverflowError, OSError):
        return "?"


def client_of(r):
    e = r.get("env", {})
    return f"{e.get('flavor') or '?'} {e.get('client') or ''} (Interface {e.get('interface') or '?'})".strip()


def evaluate(note=None):
    data = load_all()
    now = time.time()
    md = ["# Testberichte der GoldSentinel-Addons", "",
          f"Ausgewertet: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"]
    if note:
        md += ["", f"**Hinweis:** {note}"]
    md += ["", "Weg: Addon -> SavedVariables -> RaidMasterUploader -> Discord #testberichte -> hier. "
           "Neue Berichte kommen beim nächsten /reload oder Ausloggen und dem nächsten Lauf des Uploaders.", ""]
    status = {"ausgewertet": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "hinweis": note,
              "addons": {}, "offen": []}
    if not data:
        md.append("Noch keine Berichte.")
    md += ["| Addon | letzter Testlauf | Version | Client | OK | FEHLER | übersprungen | im Client prüfen | Fehler im Spiel (7 Tage) |",
           "|---|---|---|---|---|---|---|---|---|"] if data else []
    details = []
    for addon in sorted(data):
        lst = data[addon]
        tests = [r for r in lst if r.get("kind") == "test"]
        last = tests[-1] if tests else None
        # Fehler im Spiel der letzten 7 Tage, zusammengefasst
        agg = {}
        for r in lst:
            if (r.get("time") or 0) < now - 7 * 86400:
                continue
            for e in r.get("errors") or []:
                if not isinstance(e, dict):
                    continue
                k = (str(e.get("wo")), str(e.get("msg")))
                a = agg.setdefault(k, {"wo": k[0], "msg": k[1], "count": 0, "versionen": set(), "clients": set(),
                                       "zuletzt": 0, "stack": e.get("stack")})
                a["count"] += int(e.get("count") or 1)
                a["versionen"].add(str(e.get("version") or r.get("version")))
                a["clients"].add(client_of(r))
                a["zuletzt"] = max(a["zuletzt"], int(e.get("last") or r.get("time") or 0))
        errs = sorted(agg.values(), key=lambda a: -a["count"])
        c = (last or {}).get("counts", {})
        md.append(f"| {addon} | {ts(last['time']) if last else '–'} | {last.get('version') if last else '–'} | "
                  f"{client_of(last) if last else '–'} | {c.get('ok', '–')} | {c.get('fehler', '–')} | "
                  f"{c.get('uebersprungen', '–')} | {c.get('client', '–')} | {sum(a['count'] for a in errs)} |")
        st = {"berichte": len(lst), "letzter_test": last and {k: last.get(k) for k in ("id", "version", "time", "counts")},
              "fehler_tests": [], "fehler_spiel": []}
        d = [f"## {addon}", ""]
        # letzter Testlauf je Client (Forever und alter Client getrennt)
        per_client = {}
        for r in tests:
            per_client[(r.get("env", {}).get("flavor"), r.get("version"))] = r
        for (flavor, ver), r in sorted(per_client.items(), key=lambda x: x[1].get("time") or 0)[-4:]:
            cc = r.get("counts", {})
            d.append(f"**Testlauf {ver} · {client_of(r)} · {ts(r.get('time'))}** – OK {cc.get('ok')} · "
                     f"FEHLER {cc.get('fehler')} · übersprungen {cc.get('uebersprungen')} · im Client prüfen {cc.get('client')}"
                     + (f" · Sandbox {r.get('sandbox')}" if r.get("sandbox") else ""))
            for e in r.get("results") or []:
                if not isinstance(e, dict) or e.get("status") == "OK":
                    continue
                extra = " | ".join(f"{k}: {e[k]}" for k in ("lua", "ergebnis", "erwartet", "grund", "anleitung") if e.get(k))
                d.append(f"- [{e.get('status')}] {e.get('id')} {e.get('bereich')} – {e.get('name')}" + (f" ({extra})" if extra else ""))
                if e.get("status") == "FEHLER" and r is last:
                    item = {"addon": addon, "art": "test", "version": ver, "client": client_of(r), "id": e.get("id"),
                            "name": e.get("name"), "detail": extra, "bericht": r.get("id")}
                    st["fehler_tests"].append(item)
                    status["offen"].append(item)
            d.append("")
        if errs:
            d.append("**Fehler im Spiel (letzte 7 Tage)**")
            for a in errs[:30]:
                d.append(f"- {a['count']}× `{a['wo']}`: {a['msg']} – Version {', '.join(sorted(a['versionen']))} · "
                         f"{', '.join(sorted(a['clients']))} · zuletzt {ts(a['zuletzt'])}")
                item = {"addon": addon, "art": "spiel", "wo": a["wo"], "msg": a["msg"], "anzahl": a["count"],
                        "versionen": sorted(a["versionen"]), "clients": sorted(a["clients"]), "stack": a.get("stack")}
                st["fehler_spiel"].append(item)
                status["offen"].append(item)
            d.append("")
        status["addons"][addon] = st
        details += d
    # Diagnose-Protokolle (GSDIAG1) und Wegdaten (GSWEGE1): je Addon Anzahl und neueste Datei
    extra = []
    for title, base in (("Diagnose-Protokolle (GSDIAG1)", DIAG_OUT), ("Wegdaten (GSWEGE1)", WEGE_OUT)):
        rows = []
        if base.exists():
            for d in sorted(x for x in base.iterdir() if x.is_dir()):
                files = sorted(d.iterdir(), key=lambda f: f.stat().st_mtime)
                if files:
                    rel = "testberichte/" + files[-1].relative_to(OUT).as_posix()
                    rows.append(f"| {d.name} | {len(files)} | `{rel}` |")
                    status.setdefault("extras", {}).setdefault(base.name, {})[d.name] = {"anzahl": len(files), "neueste": rel}
        extra += [f"## {title}", ""]
        extra += (["| Addon | Anzahl | neueste Datei |", "|---|---|---|"] + rows) if rows else ["Noch keine."]
        extra.append("")
    md += [""] + extra + details
    OUT.mkdir(parents=True, exist_ok=True)
    new_md = redact("\n".join(md).rstrip() + "\n")
    new_js = redact(json.dumps(status, ensure_ascii=False, indent=1, default=list) + "\n")
    # nur schreiben, wenn sich ausser der Zeit etwas geändert hat (sonst alle 30 Minuten ein leerer Commit)
    stamp = re.compile(r"^(Ausgewertet: .*|  \"ausgewertet\": .*|\s*\"ausgewertet\": .*)$", re.M)
    old_md = (OUT / "status.md").read_text(encoding="utf-8") if (OUT / "status.md").exists() else ""
    if stamp.sub("", old_md) != stamp.sub("", new_md) or not (OUT / "status.json").exists():
        (OUT / "status.md").write_text(new_md, encoding="utf-8")
        (OUT / "status.json").write_text(new_js, encoding="utf-8")
    return status


def scrub_all():
    """Bereits gespeicherte Dateien nachträglich schwärzen (läuft bei jedem Lauf, nur wenn REDACT_NAMES gesetzt)."""
    if not _REDACT or not OUT.exists():
        return 0
    n = 0
    for f in OUT.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".txt", ".md"):
            t = f.read_text(encoding="utf-8", errors="replace")
            r = redact(t)
            if r != t:
                f.write_text(r, encoding="utf-8")
                n += 1
    return n


def main(argv):
    note = None
    print(f"geschwärzt: {scrub_all()} Dateien")
    if "--import" in argv:
        i = argv.index("--import")
        total = 0
        for f in argv[i + 1:]:
            if f.startswith("--"):
                break
            p = Path(f)
            raw = p.read_bytes()
            reps = from_bytes(p.name, raw)
            n = store(reps)
            total += n
            nd, nw = store_extras(*extras_from_text(raw.decode("utf-8", "replace")))
            print(f"{p.name}: {len(reps)} Berichte gefunden, {n} neu · Diagnose neu {nd} · Wegdaten neu {nw}")
        print(f"neu gespeichert: {total}")
    elif "--nur-auswerten" not in argv:
        reps, note = fetch_discord()
        if reps is not None:
            print(f"Discord: {len(reps)} Berichte gelesen, {store(reps)} neu")
            nd, nw = store_extras(*getattr(fetch_discord, "extras", ([], [])))
            print(f"Discord: Diagnose-Protokolle neu {nd} · Wegdaten neu {nw}")
        else:
            print(f"Discord: {note}")
    st = evaluate(note)
    print(f"offen: {len(st['offen'])} (testberichte/status.md)")
    if WEGE_OUT.exists() and any(WEGE_OUT.glob("*/*.json")):
        import importlib.util
        spec = importlib.util.spec_from_file_location("wege_check", Path(__file__).resolve().parent / "wege_check.py")
        wc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wc)
        rep, npc = wc.analyse(wc.load(WEGE_OUT))
        wc.write(rep, npc, WEGE_OUT / "auswertung.md")
        print(f"Wegdaten ausgewertet: {len(rep)} Zonen (testberichte/wege/auswertung.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
