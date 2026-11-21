"""daten_config.json an die Offiziere (Auftrag 21.11.2026 07:42, ab Bot 1.5.187): /uploader-daten-senden.

Der Gildenchef schickt seine daten_config.json (Zugang zum privaten Daten-Repo) per Direktnachricht an die Mitglieder mit der
Rolle "Offizier", damit ihr RaidMaster-Uploader die Addon-Daten ebenfalls hochlädt (Entscheid des Nutzers 07:39).

SICHERHEIT: Die Datei liest der Bot nur lokal (config "daten_config_path", sonst daten_config.json neben bot.py – beide nie im
Repo, .gitignore). Ihr Inhalt erscheint nirgends: nicht im Chat, nicht im Protokoll, nicht in #bot-log – nur als Anhang der
Direktnachricht. Vor dem Versand sieht der Gildenchef die Empfängerliste und muss "Senden" drücken. Jeder Offizier bekommt
die Datei einmal (gemerkt in state.json "daten_config_sent"); "erneut" schickt sie auch an die schon Belieferten.
bot.py importiert dieses Modul nach "grund.bot = bot" (/uploader-daten-senden wird beim Import angemeldet).
"""
from __future__ import annotations

import io
import json
import os

import discord
from discord import app_commands

import grund
from grund import is_chef, post_bot_log
from kern import BASE, cfg, log, state

bot = grund.bot
assert bot is not None, "datenversand_bot erst nach grund.bot = bot importieren"

OFFICER_ROLE = "offizier"
MAX_BYTES = 64 * 1024          # daten_config.json ist wenige hundert Bytes – alles Grössere ist nicht diese Datei
DM_TEXT = ("📦 **daten_config.json für den RaidMaster-Uploader** (vom Gildenchef)\n"
           "1. Datei in den Ordner des RaidMaster-Uploaders legen (neben RaidMasterUploader.exe bzw. .py).\n"
           "2. Uploader neu starten – er lädt dann auch die Addon-Daten hoch.\n"
           "⚠️ Die Datei enthält einen Zugangsschlüssel: **nicht weitergeben**, nicht in Kanäle posten.")


def config_path() -> str:
    return cfg.get("daten_config_path") or os.path.join(BASE, "daten_config.json")


def read_config() -> tuple[bytes | None, str]:
    """(Inhalt, Fehlertext). Prüft nur, dass es lesbares JSON mit "repo" und "token" ist – gibt nichts davon aus."""
    path = config_path()
    if not os.path.isfile(path):
        return None, f"Datei nicht gefunden. Lege daten_config.json hierhin: `{path}` (oder trage den Pfad in config.json als \"daten_config_path\" ein)."
    if os.path.getsize(path) > MAX_BYTES:
        return None, "Die Datei ist zu gross für eine daten_config.json – bitte die richtige Datei nehmen."
    with open(path, "rb") as f:
        raw = f.read()
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return None, "Die Datei ist kein gültiges JSON – bitte mit Daten-Repo-einrichten.bat neu erstellen."
    if not isinstance(data, dict) or not data.get("repo") or not data.get("token"):
        return None, "In der Datei fehlen \"repo\" oder \"token\" – bitte mit Daten-Repo-einrichten.bat neu erstellen."
    return raw, ""


def officers(guild, sender_id: int, again: bool) -> list:
    """Mitglieder mit der Rolle Offizier, ohne Bots und ohne den Absender; ohne "again" nur die, die sie noch nicht haben."""
    sent = set(state.data.get("daten_config_sent") or [])
    out = []
    for m in guild.members:
        if m.bot or m.id == sender_id or not any(r.name.lower() == OFFICER_ROLE for r in m.roles):
            continue
        if not again and str(m.id) in sent:
            continue
        out.append(m)
    return sorted(out, key=lambda m: m.display_name.lower())


async def send_all(members: list, raw: bytes) -> tuple[list, list]:
    """Direktnachricht mit Anhang an jeden; (erfolgreich, fehlgeschlagen)."""
    ok, failed = [], []
    for m in members:
        try:
            await m.send(DM_TEXT, file=discord.File(io.BytesIO(raw), filename="daten_config.json"))
            ok.append(m)
        except (discord.Forbidden, discord.HTTPException):
            failed.append(m)
    sent = set(state.data.get("daten_config_sent") or []) | {str(m.id) for m in ok}
    state.data["daten_config_sent"] = sorted(sent)
    state.save()
    return ok, failed


class ConfirmView(discord.ui.View):
    """Senden / Abbrechen – nur der Gildenchef, der den Befehl gegeben hat; 5 Minuten gültig."""

    def __init__(self, owner_id: int, members: list):
        super().__init__(timeout=300)
        self.owner_id, self.members, self.done = owner_id, members, False

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        return inter.user.id == self.owner_id

    @discord.ui.button(label="Senden", style=discord.ButtonStyle.danger)
    async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
        if self.done:
            return
        self.done = True
        raw, err = read_config()                       # beim Klick neu lesen: genau die Datei, die jetzt da liegt
        if raw is None:
            await inter.response.edit_message(content=f"Nicht gesendet: {err}", view=None)
            return
        await inter.response.edit_message(content="Wird gesendet …", view=None)
        ok, failed = await send_all(self.members, raw)
        text = f"✅ daten_config.json an {len(ok)} von {len(self.members)} Offizieren gesendet."
        if failed:
            text += ("\nNicht zustellbar (Direktnachrichten geschlossen): " + ", ".join(m.display_name for m in failed)
                     + " – sie können Direktnachrichten vom Server erlauben, dann den Befehl wiederholen.")
        await inter.followup.send(text, ephemeral=True)
        log.info("daten_config.json per Direktnachricht: %d gesendet, %d nicht zustellbar", len(ok), len(failed))
        await post_bot_log(f"📦 daten_config.json an {len(ok)} Offiziere gesendet"
                           + (f", {len(failed)} nicht zustellbar." if failed else "."))

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
        self.done = True
        await inter.response.edit_message(content="Abgebrochen – nichts gesendet.", view=None)


@bot.tree.command(name="uploader-daten-senden",
                  description="daten_config.json per Direktnachricht an die Offiziere senden (nur Gildenchef)")
@app_commands.describe(erneut="auch an Offiziere, die sie schon bekommen haben")
async def send_daten_config(inter: discord.Interaction, erneut: bool = False):
    if not is_chef(inter.user):
        await inter.response.send_message("Das darf nur der Gildenchef.", ephemeral=True)
        return
    raw, err = read_config()
    if raw is None:
        await inter.response.send_message(err, ephemeral=True)
        return
    if inter.guild is None or not bot.intents.members:
        await inter.response.send_message("Dafür braucht der Bot die Mitgliederliste (Server Members Intent).", ephemeral=True)
        return
    members = officers(inter.guild, inter.user.id, erneut)
    if not members:
        await inter.response.send_message("Keine Empfänger: alle Offiziere haben die Datei schon (mit `erneut:True` nochmals "
                                          "senden) oder niemand hat die Rolle Offizier.", ephemeral=True)
        return
    names = "\n".join(f"• {m.display_name}" for m in members)
    await inter.response.send_message(
        f"**daten_config.json** (Zugang zum Daten-Repo) per Direktnachricht an diese {len(members)} Offiziere senden?\n"
        f"{names}\nSie bekommen dazu die Anleitung: in den Uploader-Ordner legen, Uploader neu starten, nicht weitergeben.",
        view=ConfirmView(inter.user.id, members), ephemeral=True)
