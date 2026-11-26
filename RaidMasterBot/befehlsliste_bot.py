"""Befehlslisten (D-3 Schritt 16, ab Bot 1.5.161): #befehlsliste im Offiziersbereich und #befehle für Mitglieder –
nur der Bot schreibt, die Listen werden automatisch aktuell gehalten. COMMAND_INFO ordnet jedem Slash-Befehl
Gruppe und Bereich zu (tests/test_befehle.py prüft, dass jeder Befehl eingetragen ist).

UNVERÄNDERT aus bot.py verschoben: COMMAND_INFO, SECTION_ORDER, ADDON_COMMAND_BLOCKS, command_list_text,
_command_entries, member_command_list_text, _post_list, ensure_member_command_list, ensure_command_list.
bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt ensure_command_list.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord

import grund
import raidmaster_data as rmd
import server_setup
import updater
from gildenname_bot import name_poll
from grund import bot_guild, channel_by_id, post_bot_log
from kern import BASE, cfg, log, save_config, state

bot = grund.bot
assert bot is not None, "befehlsliste_bot erst nach grund.bot = bot importieren"


COMMAND_INFO = {
    # Befehl: (Wer, Bereich)
    "raid erstellen": ("Gildenleitung", "Raids"),
    "raid softres": ("Gildenleitung", "Raids"),
    "raid aufstellung": ("Gildenleitung", "Raids"),
    "raid liste": ("Gildenleitung", "Raids"),
    "raid schliessen": ("Gildenleitung", "Raids"),
    "raid oeffnen": ("Gildenleitung", "Raids"),
    "raid absagen": ("Gildenleitung", "Raids"),
    "raid export": ("Gildenleitung", "Raids"),
    "raid taktik": ("Gildenleitung", "Raids"),
    "raid fehlend": ("Gildenleitung", "Raids"),
    "raid grenzen": ("Gildenleitung", "Raids"),
    "raid wiederkehrend anlegen": ("Gildenleitung", "Raids"),
    "raid wiederkehrend liste": ("Gildenleitung", "Raids"),
    "raid wiederkehrend pausieren": ("Gildenleitung", "Raids"),
    "raid wiederkehrend loeschen": ("Gildenleitung", "Raids"),
    "uploader-daten-senden": ("Gildenchef", "Server"),
    "pug-einladung": ("Gildenleitung", "Raids"),
    "einladung": ("Gildenleitung", "Server"),
    "mitgliederbereich einrichten": ("Gildenleitung", "Server"),
    "mitglied aufnehmen": ("Gildenleitung", "Server"),
    "mitglied entfernen": ("Gildenleitung", "Server"),
    "charakter": ("alle", "Spieler"),
    "dkp": ("alle", "Spieler"),
    "dkpliste": ("alle", "Spieler"),
    "anwesenheit": ("alle", "Spieler"),
    "abwesend melden": ("alle", "Spieler"),
    "abwesend liste": ("alle", "Spieler"),
    "abwesend entfernen": ("alle", "Spieler"),
    "addon": ("alle", "Spieler"),
    "addon-pn": ("alle", "Spieler"),           # ab 1.5.198: PN bei neuer RaidMaster-Version ein/aus
    "raidmaster-status": ("Gildenleitung", "Verwaltung"),
    "raidmaster-einrichten": ("Gildenleitung", "Verwaltung"),
    "addon-hochladen": ("Gildenleitung", "Verwaltung"),
    "willkommen": ("Gildenleitung", "Verwaltung"),
    "uploader": ("Gildenleitung", "Verwaltung"),
    "marktdaten": ("Gildenleitung", "Verwaltung"),
    "pn": ("Gildenleitung", "Verwaltung"),
    "update": ("Gildenleitung", "Verwaltung"),
    "daten-import": ("Gildenleitung", "Verwaltung"),
    "gildenname vorschlagen": ("alle", "Spieler"),
    "gildenname hinzufuegen": ("Gildenleitung", "Verwaltung"),
    "gildenname abschliessen": ("Gildenleitung", "Verwaltung"),
    "gildenname oeffnen": ("Gildenleitung", "Verwaltung"),
    # ab Bot 1.5.106 vollständig (geprüft an den Rechteprüfungen im Code). Fehlt ein Befehl hier, steht er in
    # #befehlsliste unter "Sonstiges", in #befehle für Mitglieder aber NICHT (sicherer Standard).
    "raid testraid": ("Gildenleitung", "Raids"),
    "raid-ereignisse": ("Gildenleitung", "Raids"),
    "dkp-nachricht": ("alle", "Spieler"),
    "twink hinzufügen": ("alle", "Spieler"),
    "twink entfernen": ("alle", "Spieler"),
    "twink wechseln": ("alle", "Spieler"),
    "twink liste": ("alle", "Spieler"),
    "handwerk": ("alle", "Spieler"),
    "berufe": ("alle", "Spieler"),
    "bank": ("alle", "Spieler"),
    "rekorde": ("alle", "Spieler"),
    "ruhmeshalle-aufraeumen": ("Gildenleitung", "Verwaltung"),
    "erfolge": ("alle", "Spieler"),
    "raider-des-monats": ("alle", "Spieler"),
    "beute boss": ("alle", "Spieler"),
    "beute entfernen": ("Gildenleitung", "Verwaltung"),
    "beute export": ("Gildenleitung", "Verwaltung"),
    "beute tabellen": ("Gildenleitung", "Verwaltung"),
}
SECTION_ORDER = [("Raids", "⚔️"), ("Spieler", "👤"), ("Verwaltung", "🛠️"), ("Server", "🔗")]


# Befehle im Spiel (Addon RaidMaster) – stehen unter den Bot-Befehlen
ADDON_COMMAND_BLOCKS = [
    "🎮 **Im Spiel – Addon RaidMaster** (in den Chat tippen)\n"
    "**`/rm`** – RaidMaster-Fenster öffnen/schließen _(alle)_\n"
    "**`/rm adds`** – alle sichtbaren Adds auf einmal nach der Vorlage des Bosses markieren, z. B. Garrs Feuerschwörer "
    "(Gegner-Namensplaketten an, Taste V) _(Raidleitung/Assistenten)_\n"
    "**`/rm clear`** – alle Schlachtzugsymbole auf einmal entfernen _(Raidleitung/Assistenten)_\n"
    "**`/rm bar`** – Symbolleiste ein-/ausblenden _(alle)_\n"
    "**`/rm minimap`** – Minimap-Knopf ein-/ausblenden _(alle)_\n"
    "**`/rm sync`** – DKP-Daten von anderen Addon-Nutzern abgleichen _(alle)_\n"
    "**`/rm version`** – Addon-Version, erkannte Spielversion und Sprache anzeigen _(alle)_\n"
    "**`/rm reset`** – Fensterpositionen zurücksetzen (lädt das Interface neu) _(alle)_\n"
    "**`/rm spenden`** – RaidMaster unterstützen: zeigt den PayPal-Link zum Kopieren (auch `/rm donate`, `/rm support`) _(alle)_",
    "💬 **Im Spiel – Flüstern an den Plündermeister** (auch ohne Addon)\n"
    "**`!bid 50`** – bei einer laufenden Versteigerung 50 DKP bieten _(alle)_\n"
    "**`!dkp`** – eigenen DKP-Stand abfragen _(alle)_\n"
    "**`inv`** – an den Raidleiter flüstern: Einladung in den Raid, solange Werbung läuft _(alle)_",
    "⌨️ **Tastenbelegung im Spiel** – Esc → Tastaturbelegung → RaidMaster: Fenster, nächstes freies Symbol, "
    "einzelne Symbole, **Adds markieren**, **Alle Symbole entfernen**.",
]


def command_list_text() -> list[str]:
    """Liste aller Slash-Befehle aus dem Befehlsbaum – neue Befehle erscheinen automatisch."""
    entries = _command_entries()
    blocks = [f"📖 **Alle Bot-Befehle** · RaidMaster-Bot {updater.bot_version(BASE)}\n"
              "Tipp `/` in den Chat und such dir einen Befehl aus der Liste aus. Diese Übersicht hält der Bot selbst aktuell."]
    by_section: dict[str, list[str]] = {}
    for name, desc, params in sorted(entries):
        who, section = COMMAND_INFO.get(name, ("alle", "Sonstiges"))
        opts = (" · " + " ".join(f"`{p}`" for p in params)) if params else ""
        by_section.setdefault(section, []).append(f"**`/{name}`** – {desc} _({who})_{opts}")
    order = SECTION_ORDER + [(s, "•") for s in by_section if s not in dict(SECTION_ORDER)]
    for section, emoji in order:
        if by_section.get(section):
            blocks.append(f"{emoji} **{section}**\n" + "\n".join(by_section[section]))
    blocks.append("_Gildenleitung = Gildenchef und Rolle Offizier – nur sie dürfen im Discord etwas verändern._")
    blocks.extend(ADDON_COMMAND_BLOCKS)
    return rmd.chunk_blocks(blocks)


def _command_entries() -> list[tuple[str, str, list[str]]]:
    """Alle Befehle mit vollem Namen – ab 1.5.186 auch Untergruppen (z. B. /raid wiederkehrend anlegen)."""
    entries = []

    def walk(cmd, prefix=""):
        subs = getattr(cmd, "commands", None)
        if subs:
            for sub in subs:
                walk(sub, f"{prefix}{cmd.name} ")
        else:
            entries.append((f"{prefix}{cmd.name}", cmd.description, [p.name for p in getattr(cmd, "parameters", [])]))
    for cmd in bot.tree.get_commands():
        walk(cmd)
    return entries


def member_command_list_text() -> list[str]:
    """#befehle für alle Mitglieder: nur Befehle, die in COMMAND_INFO ausdrücklich für "alle" stehen (unbekannte nie),
    dazu die Befehle im Spiel, die alle benutzen können. Ab Bot 1.5.106."""
    lines = []
    for name, desc, params in sorted(_command_entries()):
        who, _section = COMMAND_INFO.get(name, (None, None))
        if who != "alle":
            continue
        if name.startswith("gildenname ") and name_poll().get("closed"):
            continue                                    # Abstimmung beendet: Befehl hilft niemandem mehr
        opts = (" · " + " ".join(f"`{p}`" for p in params)) if params else ""
        lines.append(f"**`/{name}`** – {desc}{opts}")
    blocks = [f"📖 **Bot-Befehle für dich** · RaidMaster-Bot {updater.bot_version(BASE)}\n"
              "Tipp `/` in irgendeinen Kanal und such dir einen Befehl aus. Die Antworten siehst meist nur du. "
              "Diese Übersicht hält der Bot selbst aktuell.",
              "👤 **Im Discord**\n" + "\n".join(lines)]
    for block in ADDON_COMMAND_BLOCKS:
        head, *rest = block.split("\n")
        mine = [ln.replace(" _(alle)_", "") for ln in rest if ln.endswith("_(alle)_")]
        if mine:
            blocks.append(head + "\n" + "\n".join(mine))
    blocks.append("_Fragen zum Addon RaidMaster? Ab damit in #addon-hilfe._")
    return rmd.chunk_blocks(blocks)


async def _post_list(channel, parts: list[str], key: str):
    """Liste in einen Kanal schreiben: vorhandene Nachrichten bearbeiten, fehlende posten, überzählige löschen."""
    old_ids = list(state.data.get(key) or [])
    new_ids = []
    no_ping = discord.AllowedMentions(roles=False, users=False, everyone=False)
    for i, text in enumerate(parts):
        if i < len(old_ids):
            try:
                await channel.get_partial_message(int(old_ids[i])).edit(content=text, allowed_mentions=no_ping)
                new_ids.append(old_ids[i])
                continue
            except discord.HTTPException:
                pass
        try:
            msg = await channel.send(text, allowed_mentions=no_ping)
        except discord.HTTPException as e:
            # 1.5.166 (Prüf-Sitzung 22:18): ein abgelehnter Teil bricht den Rest der Liste nicht ab; beim nächsten
            # Lauf fehlt seine ID und er wird erneut gepostet
            log.warning("Liste %s: Teil %d von %d nicht gepostet: %s", key, i + 1, len(parts), e)
            continue
        new_ids.append(msg.id)
    for mid in old_ids[len(parts):]:
        try:
            await channel.get_partial_message(int(mid)).delete()
        except discord.HTTPException:
            pass
    state.data[key] = new_ids
    state.save()


async def ensure_member_command_list() -> str:
    """#befehle (💬 ALLGEMEIN): anlegen, nur wenn es ihn noch nicht gibt, und die Liste aktuell halten."""
    guild = bot_guild()
    if guild is None:
        return "Befehle für Mitglieder: Server nicht gefunden."
    channel = await channel_by_id(cfg.get("member_command_channel_id"))
    if channel is None:
        if not guild.me.guild_permissions.manage_channels:
            channel = server_setup.find_channel(guild.text_channels, "befehle")
        else:
            channel, rep = await server_setup.ensure_channel_if_missing(guild, server_setup.GENERAL, "befehle",
                                                                        "RaidMaster: Bot-Befehle für Mitglieder")
            if rep:
                await post_bot_log("📖 " + "; ".join(rep))
        if channel is None:
            return "Befehle für Mitglieder: Kanal #befehle fehlt."
        cfg["member_command_channel_id"] = channel.id
        save_config()
    await _post_list(channel, member_command_list_text(), "member_command_list_messages")
    return f"✅ Befehle für Mitglieder in {channel.mention} aktuell."


async def ensure_command_list() -> str:
    guild = bot_guild()
    if guild is None:
        return "Befehlsliste: Server nicht gefunden."
    channel = await channel_by_id(cfg.get("command_list_channel_id")) or server_setup.find_channel(guild.text_channels, "befehlsliste")
    if channel is None and guild.me.guild_permissions.manage_channels:
        # ab Bot 1.5.106: fehlt #befehlsliste, legt der Bot sie selbst an (🔒 OFFIZIERE) – nur wenn es sie nicht gibt
        channel, rep = await server_setup.ensure_channel_if_missing(guild, "🔒 OFFIZIERE", "befehlsliste",
                                                                    "RaidMaster: Befehlsliste für Offiziere")
        if rep:
            await post_bot_log("📖 " + "; ".join(rep))
        if channel is not None:
            cfg["command_list_channel_id"] = channel.id
            save_config()
    member = ""
    try:
        member = " " + await ensure_member_command_list()
    except Exception:  # noqa: BLE001 – die Offiziersliste darf daran nie scheitern
        log.exception("Befehle für Mitglieder konnten nicht gepostet werden")
    if channel is None:
        return "Befehlsliste: Kanal #befehlsliste fehlt – `/raidmaster-einrichten` ausführen." + member
    # 1.5.166: dieselbe Schleife wie _post_list (bis 1.5.165 hier als Kopie) – damit gilt auch hier: ein abgelehnter
    # Teil bricht den Rest nicht ab (Frage der Prüf-Sitzung 22:18)
    await _post_list(channel, command_list_text(), "command_list_messages")
    return f"✅ Befehlsliste in {channel.mention} aktuell." + member
