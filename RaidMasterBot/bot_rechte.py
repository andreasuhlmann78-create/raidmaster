"""UP-404 (b)(c)(d): Rechte und Server-Zugehörigkeit des Bots prüfen (ab Bot 1.5.143).

Anlass: Am 15.11. ca. 01:20 war der Bot vom Gilden-Server entfernt (02:01 wieder eingeladen). Der Bot lief weiter,
aber ohne Server – jeder Zugriff endete still mit 403/404, die Uploads der Nacht kamen nicht an.

- start_check(): Liste von Meldungen beim Start und nach dem Wiedereinladen:
  * Bot auf keinem bzw. nicht auf dem eingestellten Server  -> deutliche Warnung im Protokoll
  * fehlende Rechte (Liste NEEDED)                            -> Warnung im Protokoll und in #bot-befehle
  * Rolle mit "Administrator"                                 -> Hinweis: mehr als nötig (Rolle anpassen)
- NEEDED: genau die Rechte, die der Bot benutzt (je Recht der Grund). Daraus die Zahl für den Einladungslink
  (permissions_value), damit eine neue Einladung ohne Administrator genau diese Rechte gibt.
Ohne Discord testbar (tests/test_bot_rechte.py).
"""
from __future__ import annotations

# Recht -> wofür der Bot es braucht (Grundsatz nachvollziehbar: ein Satz je Zahl/Recht)
NEEDED = {
    "view_channel": "Kanäle sehen (Anmeldungen, Uploads, Ruhmeshalle)",
    "send_messages": "Beiträge posten (Raids, Rekorde, Berichte)",
    "send_messages_in_threads": "in Bewerbungs-Threads schreiben",
    "create_private_threads": "privaten Thread je Bewerbung anlegen",
    "manage_threads": "Bewerbungs-Threads verwalten",
    "embed_links": "Kärtchen (Embeds) posten",
    "attach_files": "Dateien anhängen (Uploader, Berichte, Screenshots)",
    "read_message_history": "ältere Nachrichten lesen (Nachlesen, Aufräumen)",
    "add_reactions": "Reaktionen für Anmeldungen und Regeln",
    "manage_messages": "Nachrichten löschen/anheften (Aufräumen, #testberichte)",
    "manage_channels": "Raid-Kategorien und Kanäle anlegen",
    "manage_roles": "Rollen vergeben und Kanalrechte setzen (Mitglied, Gast, Raid-Rollen)",
    "manage_webhooks": "Uploader-Webhooks anlegen",
    "create_instant_invite": "Einladungslinks erstellen",
    "manage_guild": "Server-Einstellungen (Gildenname, Einführung)",
}


def permissions_value(names=None) -> int:
    """Bitzahl für den Einladungslink (discord.Permissions), ohne Administrator."""
    import discord
    return discord.Permissions(**{n: True for n in (names or NEEDED)}).value


def missing(perms) -> list[str]:
    """Fehlende Rechte (Namen aus NEEDED) – perms ist ein discord.Permissions-Objekt (guild.me.guild_permissions)."""
    if getattr(perms, "administrator", False):
        return []
    return [n for n in NEEDED if not getattr(perms, n, False)]


def start_check(guilds, guild_id, me_perms_of) -> list[tuple[str, str]]:
    """(Stufe, Text) – Stufe "fehler" | "warnung" | "hinweis".
    guilds: Server des Bots; guild_id: eingestellter Server (oder None); me_perms_of(guild) -> Permissions."""
    out = []
    guilds = list(guilds or [])
    if not guilds:
        out.append(("fehler", "Bot nicht auf dem Server: Der Bot ist auf keinem Discord-Server. Uploads, Anmeldungen "
                              "und Befehle gehen nicht. Bitte den Bot mit dem Einladungslink neu einladen "
                              "(ANLEITUNG, Abschnitt Bot einladen)."))
        return out
    target = None
    if guild_id:
        target = next((g for g in guilds if str(g.id) == str(guild_id)), None)
        if target is None:
            out.append(("fehler", "Bot nicht auf dem Server: Der Bot ist nicht auf dem eingestellten Gilden-Server "
                                  "(guild_id in config.json). Bitte neu einladen."))
            return out
    else:
        target = guilds[0]
    perms = me_perms_of(target)
    miss = missing(perms)
    if miss:
        out.append(("warnung", "Dem Bot fehlen Rechte: " + "; ".join(f"{n} ({NEEDED[n]})" for n in miss)
                    + ". Bitte der Rolle des Bots geben."))
    if getattr(perms, "administrator", False):
        out.append(("hinweis", "Die Rolle des Bots hat „Administrator“ – mehr als nötig. Empfohlen: Administrator "
                               "aus, dafür genau die nötigen Rechte (ANLEITUNG, Abschnitt Bot-Rechte)."))
    return out


def audit_summary(entries, bot_id: int) -> list[str]:
    """UP-404 (a): Einträge des Audit-Logs, die den Bot betreffen (entfernt, gebannt, eingeladen), als Zeilen
    "<Zeit> – <Aktion> – durch <Rolle> – Grund: <Grund>". Namen nur als höchste Rolle des Auslösers (fürs Repo
    unkritisch); entries: Objekte mit action.name, target.id, user (roles), reason, created_at."""
    labels = {"kick": "vom Server entfernt", "ban": "gebannt", "bot_add": "eingeladen", "unban": "Bann aufgehoben"}
    out = []
    for e in entries:
        act = getattr(getattr(e, "action", None), "name", "")
        if act not in labels or getattr(getattr(e, "target", None), "id", None) != bot_id:
            continue
        roles = [r for r in (getattr(e.user, "roles", None) or []) if getattr(r, "name", "") != "@everyone"]
        top = max(roles, key=lambda r: getattr(r, "position", 0)).name if roles else "ohne Rolle"
        when = e.created_at.strftime("%d.%m.%Y %H:%M UTC") if getattr(e, "created_at", None) else "?"
        out.append(f"{when} – {labels[act]} – durch Rolle „{top}“ – Grund: {getattr(e, 'reason', None) or 'keiner angegeben'}")
    return out


def needs_explicit(channel, me, everyone) -> bool:
    """UP-404 (d): Kanal/Kategorie, den der Bot ohne "Administrator" NICHT mehr sähe: für @everyone verborgen und weder
    der Bot noch eine seiner Rollen ausdrücklich freigegeben. Solche Kanäle bekommen VOR dem Entfernen von
    Administrator eine ausdrückliche Freigabe für den Bot (sonst wäre z. B. #offiziere oder #sync-daten plötzlich weg)."""
    if channel.overwrites_for(everyone).view_channel is not False:
        return False
    if channel.overwrites_for(me).view_channel is True:
        return False
    for r in getattr(me, "roles", []) or []:
        if r != everyone and channel.overwrites_for(r).view_channel is True:
            return False
    return True


BOT_ALLOW = dict(view_channel=True, send_messages=True, read_message_history=True, embed_links=True,
                 attach_files=True, add_reactions=True, manage_messages=True)

