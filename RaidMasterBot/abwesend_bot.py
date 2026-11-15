"""Abwesenheit melden (D-N1 Wunsch 1, ab Bot 1.5.184): /abwesend melden|liste|entfernen.

Jedes Mitglied meldet Zeiträume, in denen es nicht raiden kann (nur Datum, optional kurzer Grund). Die Einträge
laufen nach dem letzten Tag ab. Die Raid-Anmeldung und die Aufstellung zeigen, wer am Raidtag abwesend gemeldet ist
(nur Namen, nie den Grund; bei PUG-Raids nichts), /raid fehlend markiert diese Mitglieder. Den Grund sehen nur das
Mitglied selbst und die Gildenleitung (/abwesend liste). Der Bot schreibt niemanden an und braucht keine neuen Rechte.
Reine Funktionen: abwesenheit.py. bot.py importiert dieses Modul nach "grund.bot = bot" (/abwesend wird beim Import
angemeldet).
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

import abwesenheit
import grund
from grund import is_creator
from kern import TZ, book, log, state
from raidanzeige_bot import update_raid_message

bot = grund.bot
assert bot is not None, "abwesend_bot erst nach grund.bot = bot importieren"


def today() -> date:
    return datetime.now(ZoneInfo(TZ)).date()


def absences() -> dict:
    return state.data.setdefault("absences", {})


async def refresh_raids(start: date, end: date):
    """Offene Raids im Zeitraum neu anzeigen (Zeile "Abwesend gemeldet")."""
    for r in book.open_raids():
        day = datetime.fromtimestamp(r["start"], ZoneInfo(TZ)).date()
        if start <= day <= end:
            await update_raid_message(r)


abwesend_group = app_commands.Group(name="abwesend", description="Abwesenheit melden (z. B. Urlaub) – sieht die Raidleitung bei der Planung")


@abwesend_group.command(name="melden", description="Zeitraum melden, in dem du nicht raiden kannst")
@app_commands.describe(von="erster Tag, TT.MM. oder TT.MM.JJJJ", bis="letzter Tag, TT.MM. oder TT.MM.JJJJ",
                       grund="optional, kurz (sehen nur du und die Gildenleitung)")
async def absent_add(inter: discord.Interaction, von: str, bis: str, grund: str | None = None):
    try:
        start, end = abwesenheit.parse_range(von, bis, TZ)
    except ValueError:
        await inter.response.send_message("Datum bitte als TT.MM. oder TT.MM.JJJJ angeben, z. B. `von:20.11. bis:27.11.`",
                                          ephemeral=True)
        return
    try:
        entry = abwesenheit.add(absences(), inter.user.id, start, end, grund, today())
    except ValueError as e:
        await inter.response.send_message(str(e), ephemeral=True)
        return
    state.save()
    reason = f" ({entry['grund']})" if entry["grund"] else ""
    await inter.response.send_message(
        f"🏖️ Eingetragen: **{abwesenheit.span_text(entry)}**{reason}. Raid-Anmeldung und Aufstellung zeigen das, der "
        "Eintrag läuft danach von selbst ab. Ändern: `/abwesend liste`, `/abwesend entfernen`.", ephemeral=True)
    try:
        await refresh_raids(start, end)
    except Exception:  # noqa: BLE001
        log.exception("Raid-Anzeigen nach Abwesenheit nicht aktualisiert")


@abwesend_group.command(name="liste", description="Deine Abwesenheiten (Gildenleitung: alle)")
async def absent_list(inter: discord.Interaction):
    data = absences()
    if abwesenheit.prune(data, today()):
        state.save()
    own = data.get(str(inter.user.id)) or []
    lines = []
    if own:
        lines.append("**Deine Abwesenheiten:**")
        for i, e in enumerate(own, 1):
            lines.append(f"{i}. {abwesenheit.span_text(e)}" + (f" – {e['grund']}" if e["grund"] else ""))
    else:
        lines.append("Du hast keine Abwesenheit eingetragen (`/abwesend melden`).")
    if is_creator(inter.user):
        others = []
        for uid, entries in data.items():
            if uid == str(inter.user.id):
                continue
            m = inter.guild.get_member(int(uid)) if inter.guild else None
            p = book.profile(int(uid))
            who = (p or {}).get("name") or (m.display_name if m else f"Mitglied {uid[-4:]}")
            for e in entries:
                others.append((e["von"], f"• {who}: {abwesenheit.span_text(e)}" + (f" – {e['grund']}" if e["grund"] else "")))
        lines.append("")
        lines.append("**Alle gemeldeten Abwesenheiten:**" if others else "Sonst ist niemand abwesend gemeldet.")
        lines += [t for _, t in sorted(others)]
    text = "\n".join(lines)
    if len(text) > 1990:
        text = text[:1970].rsplit("\n", 1)[0] + "\n… (gekürzt)"
    await inter.response.send_message(text, ephemeral=True)


@abwesend_group.command(name="entfernen", description="Eine deiner Abwesenheiten löschen (Nummer aus /abwesend liste)")
@app_commands.describe(nummer="Nummer aus /abwesend liste")
async def absent_remove(inter: discord.Interaction, nummer: int):
    data = absences()
    abwesenheit.prune(data, today())
    entry = abwesenheit.remove(data, inter.user.id, nummer)
    if entry is None:
        await inter.response.send_message("Diese Nummer gibt es nicht – siehe `/abwesend liste`.", ephemeral=True)
        return
    state.save()
    await inter.response.send_message(f"Abwesenheit **{abwesenheit.span_text(entry)}** gelöscht.", ephemeral=True)
    try:
        await refresh_raids(date.fromisoformat(entry["von"]), date.fromisoformat(entry["bis"]))
    except Exception:  # noqa: BLE001
        log.exception("Raid-Anzeigen nach Abwesenheit nicht aktualisiert")


bot.tree.add_command(abwesend_group)
