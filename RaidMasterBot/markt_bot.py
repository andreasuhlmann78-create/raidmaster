"""Marktdaten im Bot (D-3 Schritt 4, ab Bot 1.5.149): Annahme der GSMARKT1-Zeilen, Nachlesen nach dem Start,
Wochen- und Tagesbericht, monatliche Blizzard-Prüfung und /marktdaten.

UNVERÄNDERT aus bot.py verschoben. Die Rechnungen stehen in market.py; hier nur das, was Discord braucht.
bot.py importiert dieses Modul erst NACH "grund.bot = bot" (der Befehl /marktdaten wird beim Import angemeldet) und
übernimmt market_intake, market_intake_safe, market_catchup, post_market_report, post_market_daily,
blizzard_monthly und market_store mit Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import io
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

import blizzard_api_check
import grund
import market
import uploader_setup
from grund import NO_PING, channel_by_id, is_creator
from kern import MARKT_DIR, TZ, cfg, log, state

bot = grund.bot
assert bot is not None, "markt_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# MN7 (ab 1.5.131): Sammelstelle für Marktdaten – siehe market.py
# ---------------------------------------------------------------------------
MARKT_EXT = re.compile(r"\.(lua|lua\.gz|json|json\.gz|gz|txt)$", re.I)
_market_store: market.Store | None = None
_market_lock = asyncio.Lock()


def market_store() -> market.Store:
    global _market_store
    if _market_store is None:
        _market_store = market.Store(MARKT_DIR)
    return _market_store


async def market_intake(message: discord.Message) -> dict:
    """GSMARKT1-Zeilen aus Anhängen und Text einer Uploader-Nachricht ablegen. Keine Antwort, kein Löschen."""
    texts = [message.content or ""]
    for a in message.attachments:
        if MARKT_EXT.search(a.filename or "") and a.size <= 25 * 1024 * 1024:
            try:
                texts.append(await asyncio.to_thread(market.text_from_bytes, a.filename, await a.read()))
            except (discord.HTTPException, OSError) as e:
                log.warning("Marktdaten: Anhang %s nicht lesbar: %s", a.filename, e)
    texts = [t for t in texts if "GSMARKT1|" in t]
    total = {"neu": 0, "doppelt": 0, "abgelehnt": 0, "begrenzt": 0, "ungueltig": 0}
    if not texts:
        return total
    fallback = market.source_key(message.webhook_id or (message.author.id if message.author else 0))
    async with _market_lock:
        st = market_store()
        for t in texts:
            src = market.source_from_text(t) or fallback        # D-MN7a: Zufallskennung des Uploaders, sonst Webhook
            for k, v in (await asyncio.to_thread(market.ingest_text, st, t, src)).items():
                total[k] += v
        if total["neu"] or total["doppelt"] or total["begrenzt"]:
            st.prune()
            await asyncio.to_thread(st.save)
    log.info("Marktdaten: %d neue Scans, %d doppelt, %d abgelehnt, %d begrenzt, %d ungültig", total["neu"],
             total["doppelt"], total["abgelehnt"], total["begrenzt"], total["ungueltig"])
    return total


async def market_intake_safe(message: discord.Message):
    try:
        await market_intake(message)
    except Exception:  # noqa: BLE001
        log.exception("Marktdaten konnten nicht gelesen werden")


async def market_catchup(minutes: int = 60) -> int:
    """D-MN7e: nach dem Start die Pakete der letzten Minuten in #testberichte nachlesen (während eines Neustarts
    kommt kein on_message). Doppelte verwirft die Ablage. Still: nie antworten, nie löschen."""
    ch = await channel_by_id(uploader_setup.tb_channel_id(cfg))
    if ch is None:
        return 0
    n = 0
    after = discord.utils.utcnow() - timedelta(minutes=minutes)
    try:
        async for m in ch.history(limit=200, after=after, oldest_first=True):
            if uploader_setup.market_source(cfg, ch.id, m.webhook_id):
                await market_intake_safe(m)
                n += 1
    except discord.HTTPException as e:      # D-MN7e2: z. B. kein Leserecht – klare Zeile statt Task-Fehler
        log.warning("Marktdaten: Nachlesen in #testberichte nicht möglich (%s %s)", getattr(e, "status", "?"),
                    getattr(e, "text", "") or type(e).__name__)
        return n
    if n:
        log.info("Marktdaten: %d Pakete der letzten %d Minuten nachgelesen", n, minutes)
    return n


async def post_market_report(now: datetime | None = None, force: bool = False) -> str | None:
    """Montags einmal: Wochenbericht der ABGESCHLOSSENEN Kalenderwoche als Anhang GSMARKTW1-<JJJJ>-W<KW>.md in den
    Bot-Kanal (D-MN7d: Name nach dieser Woche). force = Zwischenbericht der letzten 7 Tage mit eigenem Namen
    (überschreibt den Wochenbericht nicht, setzt den Montags-Merker nicht). Der Workflow markt-bericht.yml legt beide
    unter testberichte/markt/ ins Repo."""
    now = now or datetime.now(ZoneInfo(TZ))
    if not force and not market.weekly_due(now, state.data.get("market_week")):
        return None
    ch = await channel_by_id(cfg.get("botcmd_channel_id") or cfg.get("officer_channel_id"))
    if ch is None:
        return None
    fn = market.interim_report if force else market.weekly_report
    async with _market_lock:
        name, text = await asyncio.to_thread(fn, market_store(), now)
        mline = market.measure_line(await asyncio.to_thread(market.measure, market_store()))
    text += "\n" + mline + "\n"                     # KEEP90: Platz und Speicher, vom Bot selbst gemessen
    what = "Zwischenbericht" if force else "Wochenbericht"
    await ch.send(f"📈 Marktdaten-{what} (MN7, keine Namen) – wird ins Repo übernommen (testberichte/markt/).",
                  file=discord.File(io.BytesIO(text.encode("utf-8")), filename=name), allowed_mentions=NO_PING)
    if not force:
        state.data["market_week"] = market.week_key(now)
        state.save()
    return name


async def post_market_daily(now: datetime | None = None) -> str | None:
    """D-KERN1 (ab 1.5.142): einmal je Tag (nach Mitternacht, Zone des Bots) die anonyme Tages-Zusammenfassung von
    gestern als GSMARKTT1-<JJJJ-MM-TT>.json in den Bot-Kanal; der Workflow markt-bericht.yml legt sie unter
    testberichte/markt/tages/ ab. Ohne Scans an diesem Tag: nichts posten (Merker trotzdem setzen)."""
    now = now or datetime.now(ZoneInfo(TZ))
    day = market.daily_due(now, state.data.get("market_day"))
    if not day:
        return None
    async with _market_lock:
        d = await asyncio.to_thread(market.daily_summary, market_store(), day)
    state.data["market_day"] = day
    if not d["fraktionen"]:
        state.save()
        return None
    ch = await channel_by_id(cfg.get("botcmd_channel_id") or cfg.get("officer_channel_id"))
    if ch is None:
        state.data.pop("market_day", None)            # nicht verloren: nächste Stunde erneut
        return None
    data = market.dump_summary(d)
    name = market.day_name(day)
    await ch.send(f"📊 Marktdaten-Tageszusammenfassung {day} (anonym, nur Zahlen) – wird ins Repo übernommen "
                  "(testberichte/markt/tages/).", file=discord.File(io.BytesIO(data), filename=name),
                  allowed_mentions=NO_PING)
    state.save()
    log.info("Marktdaten: Tageszusammenfassung %s (%d Byte, %d weggelassen)", day, len(data), d.get("weggelassen", 0))
    return name


async def blizzard_monthly(now: datetime | None = None) -> str | None:
    """MN8 einmal im Monat wiederholen (blizzard_api_check --list). Nur bei Änderung der Realm-Listen ein Bericht
    (Anhang GSBLIZZ1-<Datum>.txt im Bot-Kanal, der Workflow übernimmt ihn). Ohne Zugang: nichts."""
    now = now or datetime.now(ZoneInfo(TZ))
    mk = market.month_key(now)
    if state.data.get("blizzard_month") == mk:
        return None
    cid, sec = cfg.get("blizzard_client_id"), cfg.get("blizzard_client_secret")
    if not cid or not sec:
        return None
    buf = io.StringIO()
    await asyncio.to_thread(blizzard_api_check.list_realms, "eu", cid, sec, buf)
    out = buf.getvalue()
    state.data["blizzard_month"] = mk
    fp = market.realm_fingerprint(out)
    if not fp:
        state.save()
        log.warning("Blizzard-Prüfung (monatlich): kein Ergebnis (Zugang prüfen)")
        return None
    old = state.data.get("blizzard_fp")
    if not old or old == fp:
        state.data["blizzard_fp"] = fp
        state.save()
        log.info("Blizzard-Prüfung (monatlich): %s", "Ausgangsstand gespeichert" if not old else "unverändert")
        return None
    # D-MN8b: Änderung erst nach erfolgreichem Senden merken – sonst nächsten Monat erneut melden
    ch = await channel_by_id(cfg.get("botcmd_channel_id") or cfg.get("officer_channel_id"))
    if ch is None:
        state.save()
        log.warning("Blizzard-Prüfung (monatlich): Änderung gefunden, aber kein Bot-Kanal – wird erneut gemeldet")
        return None
    name = f"GSBLIZZ1-{now.strftime('%Y-%m-%d')}.txt"
    text = blizzard_api_check.redact(out, cid, sec)
    await ch.send("🔎 Blizzard-Schnittstelle: Die Realm-Listen haben sich geändert (MN8 monatlich) – Bericht wird ins "
                  "Repo übernommen (testberichte/markt/).",
                  file=discord.File(io.BytesIO(text.encode("utf-8")), filename=name), allowed_mentions=NO_PING)
    state.data["blizzard_fp"] = fp
    state.save()
    return name


@bot.tree.command(name="marktdaten", description="Offiziere: Stand der Marktdaten-Sammelstelle (MN7), optional Wochenbericht jetzt")
@app_commands.describe(bericht="Zwischenbericht (letzte 7 Tage) jetzt in den Bot-Kanal legen (wird ins Repo übernommen)")
async def marktdaten_cmd(inter: discord.Interaction, bericht: bool = False):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur für den Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    st = market_store()
    heads = list(st.index["scans"].values())
    lines = [f"📈 **Marktdaten (MN7):** {len(heads)} Scans gespeichert, {int(st.index.get('dupes', 0))} doppelte "
             f"verworfen, {int(st.index.get('begrenzt', 0))} wegen Grenzen nicht abgelegt, "
             f"{int(st.index.get('verdraengt', 0))} älteste wegen Platz gelöscht (Daten bis {market.KEEP_DAYS} Tage).",
             market.measure_line(await asyncio.to_thread(market.measure, st))]
    for f, fname in market.FACTIONS.items():
        hs = [h for h in heads if h["f"] == f]
        if hs:
            last = max(h["t"] for h in hs)
            lines.append(f"- {fname}: {len(hs)} Scans, letzter "
                         f"{datetime.fromtimestamp(last, ZoneInfo(TZ)).strftime('%d.%m. %H:%M')}, "
                         f"{len({q for h in hs for q in h['q']})} Quellen")
    if bericht:
        name = await post_market_report(force=True)
        lines.append(f"Zwischenbericht **{name}** gepostet." if name
                     else "Kein Bot-Kanal gefunden – Bericht nicht gepostet.")
    await inter.followup.send("\n".join(lines), ephemeral=True)
