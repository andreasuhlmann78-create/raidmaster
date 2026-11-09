"""Dauerhafte Einladung für #willkommen (ab Bot 1.5.110, Befehl /einladung).

- Genau EIN Link: Code und URL stehen in state.data["welcome_invite_code"/"welcome_invite_url"] (nie in config.json).
- Gibt es den gespeicherten Code noch, wird KEIN neuer Link erstellt.
- Neu: ch.create_invite(max_age=0, max_uses=0, temporary=False, unique=True) – läuft nie ab, beliebig oft nutzbar.
- Danach Prüfung mit fetch_invite(code, with_expiration=True): Server, Kanal, Ablauf.
- Verboten: Einladungen löschen oder ändern, Kanäle/Rollen/Server ändern, in #willkommen posten. Dieses Modul ruft
  darum nur guild.invites(), ch.create_invite() und fetch_invite() auf (prüft tests/test_einladung.py).

Die Funktion bekommt Discord-Objekte übergeben und lässt sich offline mit Attrappen testen.
"""
from __future__ import annotations

import discord

import server_setup

CHANNEL = "willkommen"
NO_RIGHT = ("Dem Bot fehlt das Recht **Einladung erstellen** für #willkommen. Einschalten unter Servereinstellungen → "
            "Rollen → Raidmaster tool → Berechtigungen → „Einladung erstellen“ (oder in den Berechtigungen des Kanals "
            "#willkommen für die Rolle Raidmaster tool).")


async def _stored_alive(guild, code: str, fetch_invite) -> tuple[bool, object | None]:
    """Gibt es den gespeicherten Code noch? (lebt, Eintrag aus guild.invites() mit max_age oder None)"""
    if guild.me.guild_permissions.manage_guild:
        try:
            for inv in await guild.invites():
                if inv.code == code:
                    return True, inv
            return False, None
        except discord.HTTPException:
            pass
    # ohne "Server verwalten" sieht der Bot die Einladungsliste nicht: einzeln nachfragen
    try:
        await fetch_invite(code, with_expiration=True)
        return True, None
    except discord.NotFound:
        return False, None
    except discord.HTTPException:
        return True, None          # unklar (Netz) – lieber keinen zweiten Link erstellen


async def ensure_welcome_invite(guild, data: dict, fetch_invite, who: str) -> dict:
    """Dauerhaften Link für #willkommen finden oder einmal erstellen und prüfen.
    Rückgabe: {"ok": bool, "url": str|None, "created": bool, "lines": [Text …]}"""
    ch = server_setup.find_channel(guild.text_channels, CHANNEL)
    if ch is None:
        return {"ok": False, "url": None, "created": False,
                "lines": ["Kanal **#willkommen** nicht gefunden – es wird nichts angelegt."]}
    code = data.get("welcome_invite_code")
    created, entry = False, None
    alive = False
    if code:
        alive, entry = await _stored_alive(guild, code, fetch_invite)
    if not alive:
        if not ch.permissions_for(guild.me).create_instant_invite:
            return {"ok": False, "url": None, "created": False, "lines": [NO_RIGHT]}
        try:
            entry = await ch.create_invite(max_age=0, max_uses=0, temporary=False, unique=True,
                                           reason=f"Dauerhafte Einladung #willkommen ({who})")
        except discord.Forbidden:
            return {"ok": False, "url": None, "created": False, "lines": [NO_RIGHT]}
        except discord.HTTPException as e:
            return {"ok": False, "url": None, "created": False,
                    "lines": [f"Einladung konnte nicht erstellt werden ({e})."]}
        code = entry.code
        data["welcome_invite_code"] = code
        data["welcome_invite_url"] = entry.url
        created = True
    url = data.get("welcome_invite_url") or f"https://discord.gg/{code}"
    # Prüfung beim Discord-Server
    try:
        chk = await fetch_invite(code, with_expiration=True)
    except discord.HTTPException as e:
        return {"ok": False, "url": url, "created": created,
                "lines": [f"Prüfung fehlgeschlagen: Discord kennt den Link nicht ({e})."]}
    g_name = getattr(getattr(chk, "guild", None), "name", None)
    c_name = getattr(getattr(chk, "channel", None), "name", None)
    expires = getattr(chk, "expires_at", None)
    max_age = getattr(entry, "max_age", None) if entry is not None else None
    ok = g_name == guild.name and c_name == ch.name and expires is None and max_age in (0, None)
    age = "0 (unbegrenzt)" if max_age == 0 else ("nicht sichtbar (Bot ohne „Server verwalten“)" if max_age is None
                                                 else f"{max_age} s")
    lines = [f"Prüfung: Server **{g_name}**, Kanal **#{c_name}**, läuft ab: **{'nie' if expires is None else expires}**, "
             f"Gültigkeit: {age} – {'✅ in Ordnung' if ok else '⚠️ bitte ansehen'}"]
    return {"ok": ok, "url": url, "created": created, "lines": lines}


def invite_text(res: dict) -> str:
    """Antworttext für /einladung und die einmalige Meldung in #befehlsliste."""
    if not res.get("url"):
        return "🔗 **Dauerhafte Einladung #willkommen:** " + " ".join(res.get("lines") or [])
    head = "neu erstellt" if res.get("created") else "besteht schon (kein neuer Link)"
    return (f"🔗 **Dauerhafte Einladung #willkommen** ({head}): {res['url']}\n" + "\n".join(res.get("lines") or [])
            + "\nJederzeit wieder abrufbar mit `/einladung`.")
