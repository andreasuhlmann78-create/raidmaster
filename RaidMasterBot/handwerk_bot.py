"""Berufe-Verzeichnis (D-3 Schritt 23, ab Bot 1.5.170): /handwerk (wer kann das herstellen?) und /berufe – aus den
Berufen, die Addon-Nutzer einlesen (Addon: Seite Skillungen > "Meine Berufe einlesen").

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Berufe-Verzeichnis" (handwerk_cmd, berufe_cmd). bot.py
importiert dieses Modul nach "grund.bot = bot" (beide Befehle werden beim Import angemeldet).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
from symbole_bot import class_emoji

bot = grund.bot
assert bot is not None, "handwerk_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Berufe-Verzeichnis (Addon: Seite Skillungen > "Meine Berufe einlesen")
# ---------------------------------------------------------------------------
@bot.tree.command(name="handwerk", description="Wer kann das herstellen? (aus den Berufen der Addon-Nutzer)")
@app_commands.describe(suche="Teil des Namens, z. B. Feuerschutz")
async def handwerk_cmd(inter: discord.Interaction, suche: str):
    profs = rmd.professions(bot.dkp_db)
    found = rmd.find_crafters(profs, suche)
    if not profs:
        await inter.response.send_message("Noch keine Berufe bekannt – im Spiel bei RaidMaster → Skillungen → **Meine Berufe einlesen** klicken.",
                                          ephemeral=True)
        return
    if not found:
        await inter.response.send_message(f"Niemand mit RaidMaster kann „{suche}“ herstellen.", ephemeral=True)
        return
    lines = [f"🔨 **Wer kann „{suche}“ herstellen?**"]
    last = None
    for x in found:
        if x["recipe"] != last:
            lines.append(f"**{x['recipe']}**")
            last = x["recipe"]
        dot = await class_emoji(x.get("c"))
        lines.append(f"  {dot} {x['name']} – {x['prof']}" + (f" ({x['rank']})" if x.get("rank") else ""))
    for part in rmd.split_discord("\n".join(lines)):
        if not inter.response.is_done():
            await inter.response.send_message(part, ephemeral=True)
        else:
            await inter.followup.send(part, ephemeral=True)


@bot.tree.command(name="berufe", description="Berufe eines Charakters (oder aller, wenn leer)")
@app_commands.describe(name="Charaktername (leer = Übersicht der Gilde)")
async def berufe_cmd(inter: discord.Interaction, name: str | None = None):
    profs = rmd.professions(bot.dkp_db)
    if not profs:
        await inter.response.send_message("Noch keine Berufe bekannt – im Spiel bei RaidMaster → Skillungen → **Meine Berufe einlesen** klicken.",
                                          ephemeral=True)
        return
    lines = []
    if name:
        e = next((v for k, v in profs.items() if k.lower() == name.strip().lower()), None)
        if not e:
            await inter.response.send_message(f"Von {name} sind keine Berufe bekannt.", ephemeral=True)
            return
        lines.append(f"🔨 **Berufe von {name}**")
        for prof, v in sorted(e["p"].items()):
            lines.append(f"**{prof}** {v.get('r') or '?'}/{v.get('m') or '?'}" + (f" · {len(v['recipes'])} Rezepte" if v["recipes"] else ""))
    else:
        by_prof: dict[str, list] = {}
        for who, e in profs.items():
            for prof, v in e["p"].items():
                by_prof.setdefault(prof, []).append((v.get("r") or 0, who))
        lines.append("🔨 **Berufe der Gilde** (mit RaidMaster eingelesen)")
        for prof in sorted(by_prof):
            people = ", ".join(f"{w} ({r})" for r, w in sorted(by_prof[prof], reverse=True))
            lines.append(f"**{prof}:** {people}")
    parts = rmd.split_discord("\n".join(lines))
    await inter.response.send_message(parts[0], ephemeral=True)
    for part in parts[1:]:
        await inter.followup.send(part, ephemeral=True)
