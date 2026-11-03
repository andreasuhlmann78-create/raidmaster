#!/usr/bin/env python3
"""Discord-Prüfung: Steht im Discord, was im Repo liegt?

Liest mit dem Konto des RaidMaster-Bots (nur lesen, Discord-REST) die Kanäle und vergleicht:
  1. announce/<kanal>__<name>-<version>.md  – je Reihe die neueste Fassung: Ist der Text im Kanal
     (vom Bot gepostet bzw. bearbeitet)? Fehlende Zeilen werden aufgelistet.
  2. download/<Addon>-<version>.zip für die Addons, die der Bot selbst veröffentlicht (AHSentinel):
     Gibt es im Kanal den Beitrag "<Addon> <version> ist da" mit der ZIP?
Ergebnis: discord-check/status.json und discord-check/status.md (für Menschen und andere Claude-Projekte).

Umgebung: DISCORD_BOT_TOKEN (GitHub-Secret, nie in Dateien), optional DISCORD_GUILD_ID.
Der Bot-Code wird nicht verändert; die Regeln unten spiegeln RaidMasterBot/bot.py.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "discord-check")
API = "https://discord.com/api/v10"
BOT_INTERVAL_MIN = 30          # der Bot holt Änderungen etwa alle 30 Minuten
GRACE_MIN = 45                 # so lange nach dem Push gilt "noch nicht da" als "wartet"
HISTORY = 300                  # so viele Nachrichten je Kanal werden gelesen

# wie in bot.py
ANNOUNCE_VER = re.compile(r"^(?P<series>.+?)[-_ ]v?(?P<ver>\d+(?:\.\d+)+)(?P<rest>.*)$")
ANNOUNCE_CHANNELS = {"aktionshaus": "aktionshaus", "raid-addon": "raid-addon"}   # alte Dateinamen ohne "__"
EXTRA_ADDONS = {"ahsentinel": {"title": "AHSentinel", "channel": "ahsentinel"}}  # #aktionshaus gibt es nicht mehr  # Addons aus download/
PLACEHOLDER = re.compile(r"\{[@#][^{}]+\}")


def announce_series(fn):
    stem = fn[:-3] if fn.lower().endswith(".md") else fn
    if "__" not in stem:
        return None, None
    m = ANNOUNCE_VER.match(stem)
    if not m or "__" not in m.group("series"):
        return None, None
    return m.group("series").lower(), tuple(int(x) for x in m.group("ver").split("."))


class Discord:
    def __init__(self, token):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bot {token}", "User-Agent": "RaidMaster-Discord-Pruefung (github actions)"})

    def get(self, path, **params):
        for _ in range(6):
            r = self.s.get(API + path, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.2)
                continue
            if r.status_code in (401, 403):
                raise PermissionError(f"Discord {r.status_code} bei {path}")
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Discord: zu viele Anfragen bei {path}")


def pushed_minutes(path):
    """Minuten seit dem letzten Commit, der die Datei geändert hat (None = unbekannt)."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", path], cwd=ROOT,
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return int((time.time() - int(out)) / 60) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def zip_version(fn, title):
    m = re.match(re.escape(title) + r"-v?(\d+(?:\.\d+)+)\.zip$", fn, re.I)
    return m.group(1) if m else None


def main():
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    report = {"geprueft": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "commit": os.environ.get("GITHUB_SHA", "")[:7], "ok": False, "fehler": None,
              "hinweis": f"Der Bot holt Änderungen etwa alle {BOT_INTERVAL_MIN} Minuten. 'wartet' = Push ist jünger als {GRACE_MIN} Minuten.",
              "ankuendigungen": [], "addons": [], "info": []}
    if not token:
        report["fehler"] = "Secret DISCORD_BOT_TOKEN fehlt (GitHub: Settings -> Secrets and variables -> Actions)."
        return finish(report)
    dc = Discord(token)
    try:
        me = dc.get("/users/@me")
        guilds = dc.get("/users/@me/guilds")
    except PermissionError as e:
        report["fehler"] = f"Discord lehnt den Token ab ({e}) - Secret DISCORD_BOT_TOKEN prüfen."
        return finish(report)
    want = os.environ.get("DISCORD_GUILD_ID", "").strip()
    guild = next((g for g in guilds if g["id"] == want), None) if want else (guilds[0] if guilds else None)
    if not guild:
        report["fehler"] = "Der Bot ist auf keinem Server (oder DISCORD_GUILD_ID passt nicht)."
        return finish(report)
    report["server"] = guild["name"]
    all_channels = dc.get(f"/guilds/{guild['id']}/channels")
    channels = {c["name"]: c for c in all_channels if c.get("type") in (0, 5)}
    try:
        write_channel_list(guild, all_channels, report["geprueft"])
    except Exception as e:                      # die Kanalübersicht darf die eigentliche Prüfung nie stoppen
        report["info"].append({"datei": "kanaele.md", "kanal": "-", "status": f"nicht geschrieben ({e})"})
    cache = {}

    def bot_messages(name):
        if name in cache:
            return cache[name]
        ch = channels.get(name)
        if not ch:
            cache[name] = None
            return None
        msgs, before = [], None
        try:
            while len(msgs) < HISTORY:
                params = {"limit": 100}
                if before:
                    params["before"] = before
                batch = dc.get(f"/channels/{ch['id']}/messages", **params)
                if not batch:
                    break
                msgs.extend(batch)
                before = batch[-1]["id"]
                if len(batch) < 100:
                    break
        except PermissionError:
            cache[name] = "kein_zugriff"
            return cache[name]
        own = [m for m in msgs if m.get("author", {}).get("id") == me["id"]]
        cache[name] = own
        return own

    # 1) Ankündigungen: je Reihe die neueste Fassung
    adir = os.path.join(ROOT, "announce")
    # discord-check/ignorieren.txt: Dateinamen (eine pro Zeile), die absichtlich nicht (mehr) im Discord stehen
    ignore = set()
    try:
        with open(os.path.join(OUT, "ignorieren.txt"), encoding="utf-8") as f:
            ignore = {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}
    except OSError:
        pass
    newest, plain = {}, []
    for fn in sorted(os.listdir(adir)):
        if not fn.lower().endswith(".md") or fn in ignore:
            continue
        series, ver = announce_series(fn)
        if series:
            if series not in newest or ver > newest[series][1]:
                newest[series] = (fn, ver)
        else:
            plain.append(fn)
    for series, (fn, ver) in sorted(newest.items()):
        channel = fn.split("__", 1)[0].lstrip("#").lower()
        entry = check_announcement(fn, channel, bot_messages(channel))
        report["ankuendigungen"].append(entry)
    # ohne Versionsnummer: zählt mit, außer eine neuere Datei im selben Kanal hat dieselbe erste Zeile
    # (dann hat der Bot sie ersetzt). Alte Dateien ohne "__" nur zur Info.
    def title(fn):
        with open(os.path.join(adir, fn), encoding="utf-8") as f:
            t = next((ln.strip() for ln in f if ln.strip()), "")
        return re.sub(r"\s*\((?:Version|v)\s*[\d.]+\)\s*$", "", t, flags=re.I)
    def age(fn):
        m = pushed_minutes(os.path.join("announce", fn))
        return m if m is not None else 10 ** 9
    current = [fn for fn, _ in newest.values()]
    for fn in plain:
        low = fn.lower()
        channel = low.split("__", 1)[0] if "__" in low else next((v for k, v in ANNOUNCE_CHANNELS.items() if low.startswith(k + "-")), None)
        if not channel:
            continue
        e = check_announcement(fn, channel, bot_messages(channel))
        replaced = [x for x in current + plain if x != fn and x.lower().split("__", 1)[0] == low.split("__", 1)[0]
                    and title(x) == title(fn) and age(x) < age(fn)]
        if "__" in low and not replaced:
            report["ankuendigungen"].append(e)
        else:
            e["nur_info"] = ("ersetzt durch " + replaced[0]) if replaced else "alte Datei ohne Kanalnamen"
            report["info"].append(e)

    # 2) Addons, die der Bot aus download/ veröffentlicht
    ddir = os.path.join(ROOT, "download")
    for key, meta in EXTRA_ADDONS.items():
        best = None
        for fn in os.listdir(ddir):
            v = zip_version(fn, meta["title"])
            if v and (best is None or tuple(map(int, v.split("."))) > tuple(map(int, best[1].split(".")))):
                best = (fn, v)
        if not best:
            continue
        fn, v = best
        msgs = bot_messages(meta["channel"])
        e = {"addon": meta["title"], "version": v, "datei": "download/" + fn, "kanal": meta["channel"],
             "seit_push_min": pushed_minutes(os.path.join("download", fn))}
        if msgs is None:
            e["status"] = "kanal_fehlt"
        elif msgs == "kein_zugriff":
            e["status"] = "kein_zugriff"
        else:
            hit = None
            pat = re.compile(re.escape(meta["title"]) + r"\s+" + re.escape(v) + r"\*\*\s+ist da", re.I)
            for m in msgs:
                if pat.search(m.get("content") or ""):
                    hit = m
                    break
            if hit:
                names = [a.get("filename", "") for a in hit.get("attachments", [])]
                e["status"] = "ok" if any(v in n for n in names) else "zip_fehlt"
                e["gepostet"] = hit.get("timestamp", "")[:16].replace("T", " ") + " UTC"
                e["anhang"] = names
            else:
                e["status"] = "fehlt"
        settle(e)
        report["addons"].append(e)

    bad = [e for e in report["ankuendigungen"] + report["addons"] if e["status"] not in ("ok", "wartet")]
    report["ok"] = not bad
    report["wartet"] = any(e["status"] == "wartet" for e in report["ankuendigungen"] + report["addons"])
    # 3) Tut der Bot, was er soll? (nur Status, keine Inhalte – das Repo ist öffentlich)
    try:
        report["bot"] = bot_functions(all_channels, bot_messages)
    except Exception as e:
        report["bot"] = [{"pruefung": "Bot-Funktionen", "status": "fehler", "detail": str(e)[:200]}]
    if any(b["status"] not in ("ok", "wartet") for b in report["bot"]):
        report["ok"] = False
    return finish(report)


# ---------------------------------------------------------------------------
# Kanalübersicht (discord-check/kanaele.md): nur Struktur – Kategorien, Kanalnamen, Art.
# Bewusst KEINE Beiträge, Themen oder Mitgliedernamen: das Repo ist öffentlich.
# ---------------------------------------------------------------------------
KIND = {0: "Text", 2: "Sprache", 4: "Kategorie", 5: "Ankündigung", 13: "Bühne", 15: "Forum", 16: "Medien"}


def expected_channels():
    """Kanäle, die /raidmaster-einrichten anlegt (aus RaidMasterBot/server_setup.py gelesen, ohne den Bot zu laden)."""
    try:
        with open(os.path.join(ROOT, "RaidMasterBot", "server_setup.py"), encoding="utf-8") as f:
            src = f.read()
    except OSError:
        return []
    return sorted(set(m.group(2) for m in re.finditer(r'\("(text|voice|forum)",\s*"([^"]+)"', src)))


def channel_aliases():
    """CHANNEL_ALIASES aus server_setup.py: von Hand umbenannte Kanäle, die der Bot unter neuem Namen findet."""
    try:
        with open(os.path.join(ROOT, "RaidMasterBot", "server_setup.py"), encoding="utf-8") as f:
            src = f.read()
    except OSError:
        return {}
    m = re.search(r"CHANNEL_ALIASES\s*=\s*\{(.*?)\n\}", src, re.S)
    out = {}
    for k, v in re.findall(r'"([^"]+)"\s*:\s*\(([^)]*)\)', m.group(1) if m else ""):
        out[k] = re.findall(r'"([^"]+)"', v)
    return out


def channel_present(name, names):
    return name.lower() in names or any(a.lower() in names for a in channel_aliases().get(name, []))


def write_channel_list(guild, all_channels, when):
    cats = {c["id"]: c for c in all_channels if c.get("type") == 4}
    by_parent = {}
    for c in all_channels:
        if c.get("type") == 4:
            continue
        by_parent.setdefault(c.get("parent_id"), []).append(c)
    pos = lambda c: (c.get("position", 0), c["name"])
    md = ["# Discord-Kanäle", "",
          f"Stand: {when}, Server: {guild['name']}. Nur die Struktur – keine Beiträge, keine Mitglieder (das Repo ist öffentlich).",
          "Erstellt von discord-check/check.py bei jeder Discord-Prüfung.", ""]
    for c in sorted(by_parent.get(None, []), key=pos):
        md.append(f"- {'#' if c.get('type') != 2 else '🔊 '}{c['name']} ({KIND.get(c.get('type'), c.get('type'))}, ohne Kategorie)")
    for cat in sorted(cats.values(), key=pos):
        md += ["", f"## {cat['name']}", ""]
        kids = sorted(by_parent.get(cat["id"], []), key=pos)
        if not kids:
            md.append("- (leer)")
        for c in kids:
            md.append(f"- {'#' if c.get('type') != 2 else '🔊 '}{c['name']} ({KIND.get(c.get('type'), c.get('type'))})")
    names = {c["name"].lower() for c in all_channels}
    missing = [n for n in expected_channels() if not channel_present(n, names)]
    md += ["", "## Vom Bot erwartet, aber nicht da", "",
           "Kanäle aus /raidmaster-einrichten (server_setup.py), die es auf dem Server nicht gibt. Umbenannte Kanäle findet der",
           "Bot oft trotzdem (über die gespeicherte ID); die Prüfung oben sucht aber nach dem Namen.", ""]
    md += [f"- #{n}" for n in missing] or ["- keine"]
    with open(os.path.join(OUT, "kanaele.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


# ---------------------------------------------------------------------------
# Bot-Funktionen: Stimmt im Discord, was der Bot laut Repo tun soll?
# Jede Prüfung liefert nur ok/fehlt und einen kurzen Hinweis – keine Beitragstexte, keine Namen.
# ---------------------------------------------------------------------------
def _first_line(text):
    t = re.sub(r"\{#[^}]+\}", "", text or "")
    return next((ln.strip() for ln in t.splitlines() if ln.strip()), "")


def _load_json(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def bot_functions(all_channels, bot_messages):
    out = []
    names = {c["name"].lower() for c in all_channels}

    def add(pruefung, ok, detail="", status=None):
        out.append({"pruefung": pruefung, "status": status or ("ok" if ok else "fehlt"), "detail": detail})

    # a) Kanäle aus /raidmaster-einrichten
    missing = [n for n in expected_channels() if not channel_present(n, names)]
    add("Kanäle aus /raidmaster-einrichten", not missing, ("fehlen: " + ", ".join("#" + n for n in missing)) if missing else "alle da")

    # b) Regel-Kanäle (guild_rules.json): Kanal da und jeder Beitrag (erste Zeile) vom Bot gepostet
    rules = (_load_json("RaidMasterBot/guild_rules.json") or {}).get("channels") or []
    for r in rules:
        key = r.get("key")
        if not key:
            continue
        if key.lower() not in names:
            add(f"Regeln #{key}", False, "Kanal fehlt")
            continue
        msgs = bot_messages(key)
        if msgs == "kein_zugriff":
            add(f"Regeln #{key}", False, "Bot darf den Kanal nicht lesen", "kein_zugriff")
            continue
        texts = [m.get("content") or "" for m in (msgs or [])]
        heads = [_first_line(p) for p in r.get("posts") or []]
        miss = sum(1 for h in heads if h and not any(h in t for t in texts))
        add(f"Regeln #{key}", miss == 0, f"{len(heads) - miss}/{len(heads)} Beiträge da" if heads else "keine Beiträge vorgesehen")

    # c) Gildenbank: nur noch #gildenbank, oben Regeln, darunter der Bestand
    if "gildenbank-bestand" in names:
        add("Gildenbank: #gildenbank-bestand aufgelöst", False, "Kanal gibt es noch (löscht der Bot ab 1.5.96 nur, wenn darin nur Bot-Beiträge stehen)")
    else:
        add("Gildenbank: #gildenbank-bestand aufgelöst", True, "Kanal weg")
    gb = bot_messages("gildenbank")
    if gb is None:
        add("Gildenbank: Bestand unter den Regeln", False, "#gildenbank fehlt")
    elif gb == "kein_zugriff":
        add("Gildenbank: Bestand unter den Regeln", False, "Bot darf #gildenbank nicht lesen", "kein_zugriff")
    else:
        rule_head = next((_first_line(p) for r in rules if r.get("key") == "gildenbank" for p in r.get("posts") or []), "")
        # API liefert neueste zuerst
        idx_bank = next((i for i, m in enumerate(gb) if (m.get("content") or "").startswith("📦 **Bestand der Gildenbank**")), None)
        idx_rule = next((i for i, m in enumerate(gb) if rule_head and rule_head in (m.get("content") or "")), None)
        if idx_bank is None:
            add("Gildenbank: Bestand unter den Regeln", False, "kein Bestands-Beitrag in #gildenbank")
        elif idx_rule is None:
            add("Gildenbank: Bestand unter den Regeln", False, "Regel-Beitrag fehlt in #gildenbank")
        else:
            add("Gildenbank: Bestand unter den Regeln", idx_bank < idx_rule,
                "Reihenfolge stimmt" if idx_bank < idx_rule else "Bestand steht über den Regeln")

    # d) Raids von WoW Forever: Kanäle je Raid
    raids = _load_json("RaidMasterBot/forever_raids.json") or {}
    raids = raids.get("raids", raids) if isinstance(raids, dict) else raids
    for r in raids if isinstance(raids, list) else []:
        if not isinstance(r, dict) or not r.get("forever"):
            continue
        p = r.get("prefix") or r.get("key")
        want = [f"{p}-anmeldung", f"{p}-taktik", f"{p}-dkp", f"{p}-loot", f"einteilung-{p}"]
        want += [f"{p}-{e['name']}" for e in r.get("extra_channels") or [] if e.get("name")]
        miss = [w for w in want if w.lower() not in names]
        add(f"Raid {r.get('name') or p}", not miss, ("fehlen: " + ", ".join("#" + m for m in miss)) if miss else "alle Kanäle da")
    return out


def check_announcement(fn, channel, msgs):
    path = os.path.join(ROOT, "announce", fn)
    e = {"datei": "announce/" + fn, "kanal": channel, "seit_push_min": pushed_minutes(os.path.join("announce", fn))}
    if msgs is None:
        e["status"] = "kanal_fehlt"
        return settle(e)
    if msgs == "kein_zugriff":
        e["status"] = "kein_zugriff"
        return e
    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.read().strip().splitlines() if ln.strip()]
    text = "\n".join(m.get("content") or "" for m in msgs)
    missing = []
    for ln in lines:
        segs = [s.strip() for s in PLACEHOLDER.split(ln) if len(s.strip()) >= 3]
        if segs and not all(s in text for s in segs):
            missing.append(ln)
    total = max(1, len(lines))
    e["abdeckung"] = round(1 - len(missing) / total, 3)
    if not missing:
        e["status"] = "ok"
    elif len(missing) == total:
        e["status"] = "fehlt"
    else:
        e["status"] = "veraltet"
        e["fehlende_zeilen"] = [m[:160] for m in missing[:5]]
    return settle(e)


def settle(e):
    """Noch nicht da, aber frisch gepusht: 'wartet' statt Fehler."""
    if e["status"] in ("fehlt", "veraltet", "zip_fehlt", "kanal_fehlt") and e.get("seit_push_min") is not None \
            and e["seit_push_min"] < GRACE_MIN:
        e["status_eigentlich"] = e["status"]
        e["status"] = "wartet"
    return e


ICON = {"fehler": "❌", "ok": "✅", "wartet": "⏳", "veraltet": "⚠️", "fehlt": "❌", "zip_fehlt": "❌", "kanal_fehlt": "❌", "kein_zugriff": "🔒"}


def finish(report):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "status.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    md = ["# Discord-Prüfung", "",
          f"Geprüft: {report['geprueft']} (Commit {report.get('commit') or '?'})" + (f", Server: {report['server']}" if report.get("server") else ""),
          ""]
    if report.get("fehler"):
        md += [f"**❌ Prüfung nicht möglich:** {report['fehler']}", ""]
    else:
        md += ["**Ergebnis: " + ("✅ alles im Discord" if report["ok"] and not report.get("wartet")
                                 else "⏳ alles da oder unterwegs (Bot hat noch nicht abgeholt)" if report["ok"]
                                 else "❌ es fehlt etwas") + "**", "", report["hinweis"], ""]
        if report["addons"]:
            md += ["## Addon-Veröffentlichungen (download/)", "", "| | Addon | Version | Kanal | Gepostet | seit Push |", "|---|---|---|---|---|---|"]
            for e in report["addons"]:
                md.append(f"| {ICON.get(e['status'], '?')} {e['status']} | {e['addon']} | {e['version']} | #{e['kanal']} | "
                          f"{e.get('gepostet', '-')} | {fmt_min(e.get('seit_push_min'))} |")
            md.append("")
        md += ["## Ankündigungen (announce/, neueste Fassung je Reihe)", "", "| | Datei | Kanal | Abdeckung | seit Push |", "|---|---|---|---|---|"]
        for e in report["ankuendigungen"]:
            md.append(f"| {ICON.get(e['status'], '?')} {e['status']} | {e['datei'].split('/', 1)[1]} | #{e['kanal']} | "
                      f"{int(e.get('abdeckung', 0) * 100)} % | {fmt_min(e.get('seit_push_min'))} |")
        for e in report["ankuendigungen"]:
            if e.get("fehlende_zeilen"):
                md += ["", f"**{e['datei']}** – fehlt im Discord:"] + [f"- `{z}`" for z in e["fehlende_zeilen"]]
        if report.get("bot"):
            md += ["", "## Bot-Funktionen (tut der Bot, was er soll?)", "", "| | Prüfung | Ergebnis |", "|---|---|---|"]
            for b in report["bot"]:
                md.append(f"| {ICON.get(b['status'], '?')} {b['status']} | {b['pruefung']} | {b.get('detail', '')} |")
        if report["info"]:
            md += ["", "## Nur zur Info (ohne Versionsnummer)", ""]
            for e in report["info"]:
                md.append(f"- {ICON.get(e['status'], '?')} {e['datei']} in #{e['kanal']}: {e['status']}")
    with open(os.path.join(OUT, "status.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


def fmt_min(m):
    if m is None:
        return "?"
    if m < 120:
        return f"{m} Min."
    if m < 48 * 60:
        return f"{m // 60} Std."
    return f"{m // 1440} Tage"


if __name__ == "__main__":
    sys.exit(main())
