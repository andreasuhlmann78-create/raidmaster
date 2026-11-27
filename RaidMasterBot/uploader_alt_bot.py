"""D-UPALT (ab Bot 1.5.193, Auftrag Supervisor 24.11.2026 10:05; Entscheid des Nutzers 24.11. 07:22 "wenn jemand nicht die
neuste version drauf hatt die daten nicht mehr annehmen!"): Besitzer eines Rechners mit veraltetem Daten-Uploader per PN
informieren.

D-UPMIN1 (ab Bot 1.5.195, Supervisor 24.11. 21:32): Massgebend ist die NÖTIGE Version (required): Mindestversion aus
RaidMasterUploader/mindestversion.txt, mindestens aber 2.3.23 – Uploader 2.3.20–2.3.22 nehmen selbst nur die neueste an und
liefern darum nicht, solange es eine neuere gibt. 1 PN je Rechner und nötiger Version: steigt die Mindestversion nicht, kommt
für eine neue kleine Version keine PN (D-UPD1 Punkt 1). Text "(mindestens Version y)".
D-UPD1 (ab Bot 1.5.196, Supervisor 21:36): Haben alle betroffenen Rechner eines Mitglieds schon 2.3.24 (Rückfrage j/n, UP-UPD1),
lautet die PN "Neue Pflicht-Version … mit j bestätigen (oder /uploader holen)". stand.json "update" je Rechner: fehlgeschlagen ->
PN an den Besitzer mit Grund und "/uploader holen"; erfolgreich -> nur Zahl in #bot-log. Je Rechner und Zeit einmal
(state.json "upd_gemeldet"), nur Ergebnisse der letzten 6 Stunden.

Uploader ab 2.3.20 nehmen nur noch Daten der neuesten Uploader-Version an und zeigen das selbst an. Rechner mit einem Uploader
VOR 2.3.20 können das nicht anzeigen – darum schreibt der Bot dem Besitzer:
  "Dein Daten-Uploader ist veraltet – deine Daten werden nicht mehr angenommen. Bitte /uploader holen (neueste Version x.y.z)."

Ablauf (alle 30 Minuten, uploader_alt_loop):
1. Neueste Version = VERSION in RaidMasterUploader/uploader.py im Repo (update_repo, dieselbe Quelle wie /uploader).
2. stand.json des Daten-Repos aus den Zweigen "sicherung" UND main (Zugang: daten_config.json auf dem Server, nur gelesen,
   nie ausgegeben). Je Rechner zählt der Eintrag mit der grössten "zeit". Veraltet = Feld "uploader" fehlt, "unbekannt" oder
   älter als die neueste Version.
3. Zuordnung Rechner -> Discord-Mitglied: nur aus den privaten #sync-daten-Kanälen (cfg["sync"][Mitglied] -> Index-Nachricht
   des Abgleichs; dort stehen die Rechnernamen). Steht ein Rechner bei zwei Mitgliedern oder bei keinem: keine PN, nur eine
   Zahl in #bot-log (einmal je Rechner und Version, state.json "upalt_gemeldet"); die PN folgt, sobald der Besitzer
   eindeutig ist. Nichts davon kommt ins Repo.
4. Höchstens 1 PN je Rechner und neuester Uploader-Version (state.json "upalt_pn": {Rechner: Version}). Nie an Gäste
   (Rolle "Gast") und Bots. Hat das Mitglied die neueste Version schon per /uploader vom Bot bekommen
   (state.json "uploader_geschickt", ab 1.5.193 gemerkt), wird es nicht nochmals angeschrieben.
5. Erster Lauf (state.json hat noch kein "upalt_pn") und neueste Version 2.3.20: Alle dann veralteten Rechner gelten als
   schon informiert (Stand 24.11. 10:00: PC des Gildenchefs und 2 Offiziere; die Offiziere haben 2.3.20 um 08:37 per Bot
   bekommen, Auftrag: NICHT nochmals anschreiben, solange keine neuere Version erscheint). Ab 2.3.21 gilt wieder Punkt 4.
#bot-log und Protokoll nennen nur Zahlen, nie Rechner- oder Spielernamen.
"""
from __future__ import annotations

import json
import re

import discord
from discord.ext import tasks

import grund
import uploader_version
from grund import bot_guild, channel_by_id, post_bot_log
from kern import cfg, log, state

bot = grund.bot
assert bot is not None, "uploader_alt_bot erst nach grund.bot = bot importieren"

MIN_LOGIK_AB = "2.3.23"            # D-UPMIN1: ab dieser Uploader-Version gilt die Mindestversion (UP-MIN1); 2.3.20–2.3.22
                                   # nehmen selbst nur die neueste an
SEED_VERSION = "2.3.20"            # Punkt 5: an diese Version haben die Offiziere die ZIP schon am 24.11. 08:37 bekommen
INDEX_MARK = "GSSYNC-INDEX"        # wie RaidMasterUploader/sync.py
GUEST_ROLE = "gast"
BRANCHES = ("sicherung", None)     # None = Standardzweig (main)
API = "https://api.github.com"
VERSION_OK = re.compile(r"^\d+(?:\.\d+){1,3}$")
UPD_AB = "2.3.24"                  # D-UPD1: ab dieser Version fragt der Uploader selbst "installieren? (j/n)" (UP-UPD1)
AUTO_AB = "2.3.29"                 # DC-UPD1: ab dieser Version installiert der Uploader neue (stabile) Versionen ohne Frage (RM-UPD2)
PN_TEXT_AUTO = ("⚠️ Neue Pflicht-Version des Uploaders (mindestens Version {neu}) – dein Uploader installiert sie selbst, sobald er "
                "läuft (bitte starten). Klappt das nicht: /uploader holen.")
PN_TEXT_J = ("⚠️ Neue Pflicht-Version des Uploaders (mindestens Version {neu}) – bitte im Uploader-Fenster mit j bestätigen "
             "(oder /uploader holen).")
UPD_FAIL_TEXT = ("❌ Uploader-Update fehlgeschlagen ({grund}) – die alte Version {von} läuft weiter. Bitte /uploader holen.")
UPD_FRISCH = 6 * 3600              # D-UPD1: nur Update-Ergebnisse der letzten 6 Stunden melden (ältere: einmal still gemerkt)
PN_TEXT = ("⚠️ Dein Daten-Uploader ist veraltet – deine Daten werden nicht mehr angenommen. "
           "Bitte /uploader holen (mindestens Version {neu}).")


def path_name(name: str) -> str:
    """Ordnername eines Rechners im Daten-Repo – gleiche Regel wie RaidMasterUploader/daten.py path_name."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(name)).strip("._") or "rechner"


def clean_version(v) -> str | None:
    """Gültige Versionsnummer oder None ("unbekannt", leer, fehlt)."""
    v = str(v or "").strip()
    return v if VERSION_OK.match(v) else None


def parse_minimum(text: str | None) -> str | None:
    """Erste Zeile ohne # in RaidMasterUploader/mindestversion.txt (wie der Uploader 2.3.23 sie liest)."""
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            return clean_version(ln)
    return None


def required(newest: str, minimum: str | None) -> str | None:
    """D-UPMIN1: Welche Version ein Rechner mindestens braucht, damit seine Daten angenommen werden.
    - neueste < 2.3.23 (noch keine Mindestversion): die neueste (Regel von 2.3.20–2.3.22).
    - sonst max(Mindestversion, 2.3.23): Rechner mit 2.3.20–2.3.22 liefern nicht, solange es eine neuere gibt (sie prüfen selbst
      gegen die neueste) – erst ab 2.3.23 zählt die Mindestversion. Mindestversion nicht lesbar -> None (Lauf auslassen)."""
    if uploader_version.is_older(newest, MIN_LOGIK_AB):
        return newest
    if not minimum:
        return None
    return MIN_LOGIK_AB if uploader_version.is_older(minimum, MIN_LOGIK_AB) else minimum


def is_outdated(entry: dict, newest: str) -> bool:
    return uploader_version.is_older(clean_version(entry.get("uploader")), newest)


def merge_stands(*stands: dict | None) -> dict:
    """Je Rechner der Eintrag mit der grössten "zeit" aus allen gelesenen stand.json (sicherung und main)."""
    out: dict = {}
    for st in stands:
        if not isinstance(st, dict):
            continue
        for k, v in st.items():
            if not isinstance(v, dict):
                continue
            try:
                z = int(v.get("zeit") or 0)
            except (TypeError, ValueError):
                z = 0
            if k not in out or z > out[k][0]:
                out[k] = (z, v)
    return {k: v for k, (_, v) in out.items()}


def outdated(stand: dict, newest: str) -> dict[str, str]:
    """{Rechner: Version oder ""} aller Rechner mit veraltetem Uploader."""
    return {k: (clean_version(v.get("uploader")) or "") for k, v in stand.items() if is_outdated(v, newest)}


def machines_in_index(content: str) -> set[str]:
    """Rechner (als Ordnername) aus der Index-Nachricht des Abgleichs (#sync-daten): "machine" und je Eintrag Feld 3."""
    m = re.search(r"\{.*\}", content or "", re.S)
    if not m:
        return set()
    try:
        idx = json.loads(m.group(0))
    except ValueError:
        return set()
    if not isinstance(idx, dict):
        return set()
    names = [idx.get("machine")]
    r = idx.get("r")
    if isinstance(r, dict):
        names += [e[2] for e in r.values() if isinstance(e, list) and len(e) >= 3]
    return {path_name(n) for n in names if isinstance(n, str) and n.strip()}


def owners(index_by_member: dict[int, set[str]]) -> tuple[dict[str, int], set[str]]:
    """({Rechner: Mitglied}, mehrdeutige Rechner). Ein Rechner bei zwei Mitgliedern bekommt keinen Besitzer."""
    seen: dict[str, set[int]] = {}
    for uid, machines in index_by_member.items():
        for mach in machines:
            seen.setdefault(mach, set()).add(uid)
    return ({k: next(iter(v)) for k, v in seen.items() if len(v) == 1},
            {k for k, v in seen.items() if len(v) > 1})


def pn_text(newest: str, versions: list[str]) -> str:
    """D-UPD1 Punkt 1: Haben alle betroffenen Rechner schon die Rückfrage (ab 2.3.24), reicht "mit j bestätigen"; sonst
    muss die ZIP einmal von Hand installiert werden (/uploader)."""
    def ab(grenze):
        return bool(versions) and all(not uploader_version.is_older(clean_version(v), grenze) for v in versions)
    if ab(AUTO_AB):                         # DC-UPD1 (ab 1.5.199): ab 2.3.29 ohne Frage
        return PN_TEXT_AUTO.format(neu=newest)
    if ab(UPD_AB):
        return PN_TEXT_J.format(neu=newest)
    return PN_TEXT.format(neu=newest)


def update_events(stand: dict, seen: dict, now: float) -> tuple[dict, dict]:
    """D-UPD1 Punkt 2: ({Rechner: update-Eintrag} neu zu meldende, {Rechner: zeit} alle gesehenen). stand.json je Rechner
    "update": {"von", "nach", "ergebnis" ("ok" | "fehlgeschlagen: <Grund>"), "zeit"}. Je Rechner und Zeit nur einmal;
    älter als UPD_FRISCH: nur merken, nicht melden (z. B. beim ersten Lauf)."""
    new, seen = {}, dict(seen)
    for k, v in stand.items():
        u = v.get("update") if isinstance(v, dict) else None
        if not isinstance(u, dict):
            continue
        try:
            z = int(u.get("zeit") or 0)
        except (TypeError, ValueError):
            continue
        if not z or seen.get(k) == z:
            continue
        seen[k] = z
        if now - z <= UPD_FRISCH:
            new[k] = u
    return new, seen


def plan(old: dict[str, str], newest: str, own: dict[str, int], sent: dict[str, str], given: dict[str, str],
         is_guest) -> dict:
    """Was zu tun ist. Ergebnis: {"pn": {Mitglied: [Rechner]}, "skip": {Rechner: Grund}, "unknown": [Rechner]}.
    sent: {Rechner: Version, für die schon eine PN ging}; given: {Mitglied: Version per /uploader};
    is_guest(Mitglied) -> True/False/None (None = nicht mehr auf dem Server)."""
    out = {"pn": {}, "skip": {}, "unknown": []}
    for mach in sorted(old):
        if sent.get(mach) == newest:
            continue
        uid = own.get(mach)
        if uid is None:
            out["unknown"].append(mach)
            continue
        if not uploader_version.is_older(clean_version(given.get(str(uid))), newest):
            out["skip"][mach] = "per /uploader bekommen"
            continue
        g = is_guest(uid)
        if g is None:
            out["skip"][mach] = "nicht auf dem Server"
        elif g:
            out["skip"][mach] = "Gast"
        else:
            out["pn"].setdefault(uid, []).append(mach)
    return out


def note_given(member_id: int, version: str | None):
    """Von /uploader aufgerufen: Mitglied hat diese Uploader-ZIP per Bot bekommen (Punkt 4)."""
    if not clean_version(version):
        return
    given = state.data.setdefault("uploader_geschickt", {})
    if uploader_version.is_older(clean_version(given.get(str(member_id))), version):
        given[str(member_id)] = version
        state.save()


async def _get_text(session, url: str, what: str, headers: dict | None = None) -> str | None:
    async with session.get(url, headers=headers or {}) as resp:
        if resp.status != 200:
            log.info("D-UPALT: %s – Antwort %d", what, resp.status)
            return None
        return await resp.text()


async def read_stands(session, repo: str, token: str) -> list[dict]:
    """stand.json aus "sicherung" und main. Der Zugangsschlüssel steht nie in einer Meldung."""
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github.raw+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "RaidMasterBot"}
    out = []
    for ref in BRANCHES:
        url = f"{API}/repos/{repo}/contents/stand.json" + (f"?ref={ref}" if ref else "")
        text = await _get_text(session, url, f"stand.json ({ref or 'main'})", headers)
        if text is None:
            continue
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if isinstance(data, dict):
            out.append(data)
    return out


async def read_indexes() -> dict[int, set[str]]:
    """Rechner je Mitglied aus den Index-Nachrichten der privaten #sync-daten-Kanäle."""
    out: dict[int, set[str]] = {}
    for uid, entry in (cfg.get("sync") or {}).items():
        if not isinstance(entry, dict) or not entry.get("channel_id") or not entry.get("index_id"):
            continue
        ch = await channel_by_id(entry["channel_id"])
        if ch is None:
            continue
        try:
            msg = await ch.fetch_message(int(entry["index_id"]))
        except (discord.HTTPException, ValueError):
            continue
        machines = machines_in_index(msg.content or "")
        if machines:
            out[int(uid)] = machines
    return out


async def check_once() -> dict | None:
    """Ein Lauf. Liefert das Ergebnis (für Tests/Protokoll) oder None, wenn etwas Nötiges fehlt (nächster Lauf in 30 Min)."""
    import aiohttp
    import datenversand_bot
    repo = (cfg.get("update_repo") or "").strip()
    guild = bot_guild()
    if not repo or guild is None:
        return None
    raw, _err = datenversand_bot.read_config()
    if raw is None:
        return None
    try:
        conf = json.loads(raw.decode("utf-8-sig"))
        data_repo, token = str(conf["repo"]).strip(), str(conf["token"]).strip()
    except (ValueError, KeyError, UnicodeDecodeError):
        return None
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        text = await _get_text(session, uploader_version.raw_url(repo, "RaidMasterUploader/uploader.py"), "uploader.py")
        latest = clean_version(uploader_version.parse_version(text or ""))
        if not latest:
            return None
        minimum = None
        if not uploader_version.is_older(latest, MIN_LOGIK_AB):
            minimum = parse_minimum(await _get_text(
                session, uploader_version.raw_url(repo, "RaidMasterUploader/mindestversion.txt"), "mindestversion.txt"))
        newest = required(latest, minimum)        # ab hier: die NÖTIGE Version (D-UPMIN1), Schlüssel für "1 PN je Rechner"
        if not newest:
            return None
        stands = await read_stands(session, data_repo, token)
    if not stands:
        return None
    merged = merge_stands(*stands)
    old = outdated(merged, newest)
    import time as _time
    events, seen_upd = update_events(merged, state.data.get("upd_gemeldet") or {}, _time.time())
    sent = state.data.get("upalt_pn")
    if sent is None:                                   # Punkt 5: erster Lauf
        sent = {}
        if newest == SEED_VERSION:
            sent = {k: newest for k in old}
        state.data["upalt_pn"] = sent
        state.save()
        if sent:
            log.info("D-UPALT: erster Lauf, %d Rechner gelten für %s als informiert", len(sent), newest)
            await post_bot_log(f"📦 Uploader-Prüfung eingeschaltet: {len(sent)} Rechner mit altem Uploader – "
                               f"{SEED_VERSION} wurde ihnen schon geschickt, keine PN bis zur nächsten Version.")
    if not old and not events:
        if seen_upd != (state.data.get("upd_gemeldet") or {}):
            state.data["upd_gemeldet"] = seen_upd
            state.save()
        return {"newest": newest, "latest": latest, "old": 0, "pn": 0, "fail": 0, "unknown": 0, "upd_ok": 0, "upd_fail": 0}
    own, ambiguous = owners(await read_indexes())

    def is_guest(uid):
        m = guild.get_member(uid)
        if m is None:
            return None
        return bool(m.bot) or any((r.name or "").strip().casefold() == GUEST_ROLE for r in m.roles)

    todo = plan(old, newest, own, sent, state.data.get("uploader_geschickt") or {}, is_guest)
    ok = fail = 0
    for uid, machines in todo["pn"].items():
        member = guild.get_member(uid)
        text = pn_text(newest, [old[m] for m in machines]) + "\nBetroffen: " + ", ".join(f"`{m}`" for m in machines)
        try:
            await member.send(text, allowed_mentions=discord.AllowedMentions.none())
            ok += 1
        except discord.HTTPException:
            fail += 1
        for mach in machines:                           # höchstens 1 PN (bzw. 1 Versuch) je Rechner und Version
            sent[mach] = newest
    for mach in todo["skip"]:
        sent[mach] = newest
    told = state.data.setdefault("upalt_gemeldet", {})  # ohne Besitzer: einmal je Rechner und Version in #bot-log;
    new_unknown = [m for m in todo["unknown"] if told.get(m) != newest]   # PN folgt, sobald der Besitzer bekannt ist
    for mach in new_unknown:
        told[mach] = newest
    upd_ok = upd_fail = upd_pn = 0                       # D-UPD1 Punkt 2: Ergebnis der Updates per Knopfdruck
    for mach, u in sorted(events.items()):
        if str(u.get("ergebnis") or "") == "ok":
            upd_ok += 1                                  # Bestätigung nur als Zahl in #bot-log (der Nutzer sieht es im Fenster)
            continue
        upd_fail += 1
        uid = own.get(mach)
        if uid is None or is_guest(uid) is not False:
            continue
        grund = str(u.get("ergebnis") or "").split(":", 1)[-1].strip() or "unbekannt"
        try:
            await guild.get_member(uid).send(
                UPD_FAIL_TEXT.format(grund=grund[:300], von=clean_version(u.get("von")) or "?") + f"\nRechner: `{mach}`",
                allowed_mentions=discord.AllowedMentions.none())
            upd_pn += 1
        except discord.HTTPException:
            pass
    state.data["upd_gemeldet"] = seen_upd
    state.data["upalt_pn"] = sent
    state.save()
    if upd_ok or upd_fail:
        await post_bot_log(f"🔄 Uploader-Update per Knopfdruck: {upd_ok} erfolgreich, {upd_fail} fehlgeschlagen"
                           + (f" ({upd_pn} PN geschickt)" if upd_fail else "") + ".")
    unknown = len(new_unknown)
    if ok or fail or unknown:
        parts = [f"{ok} PN geschickt"]
        if fail:
            parts.append(f"{fail} nicht zustellbar (Direktnachrichten geschlossen)")
        if unknown:
            parts.append(f"{unknown} Rechner ohne eindeutigen Besitzer"
                         + (f" ({len(ambiguous & set(new_unknown))} bei mehreren Mitgliedern)"
                            if ambiguous & set(new_unknown) else "")
                         + " – keine PN")
        log.info("D-UPALT %s: %s", newest, "; ".join(parts))
        await post_bot_log(f"📦 Alter Daten-Uploader (nötig: mindestens {newest}): " + "; ".join(parts) + ".")
    return {"newest": newest, "latest": latest, "old": len(old), "pn": ok, "fail": fail, "unknown": unknown,
            "upd_ok": upd_ok, "upd_fail": upd_fail}


@tasks.loop(minutes=30)
async def uploader_alt_loop():
    try:
        await check_once()
    except Exception as e:  # noqa: BLE001 – Netz usw.; nächster Lauf in 30 Minuten
        log.warning("D-UPALT: %s", type(e).__name__)


@uploader_alt_loop.before_loop
async def _before():
    await bot.wait_until_ready()
