"""Grundregeln am echten Server prüfen – nur lesen (ab Bot 1.5.125, Auftrag TU5).

Der Bot ruft check() beim Start und alle 6 Stunden auf. Jede Verletzung kommt als "GRUNDREGEL VERLETZT …" ins
Protokoll (und einmal je Meldung nach #bot-befehle), ohne Spielernamen – so sieht die Prüf-Sitzung echte Fehler, bevor
ein Spieler sie bemerkt. Nichts wird geändert.
"""
from __future__ import annotations

import member_area

OFFICER_CATEGORY = "🔒 OFFIZIERE"
ADDON_CATEGORY = "Addon's by GoldSentinel"


def _fold(s: str) -> str:
    return (s or "").strip().casefold()


def _cat(guild, name):
    return next((c for c in guild.categories if _fold(c.name) == _fold(name)), None)


def check(guild, cfg: dict) -> list[str]:
    """Liste der Verletzungen (leer = alles gut)."""
    out: list[str] = []
    me = guild.me
    everyone = guild.default_role
    # 1) Der Bot darf in allen Anmeldekanälen posten (Befund R1: Raid ohne Nachricht)
    ids = []
    for pool, chans in (cfg.get("raid_channels") or {}).items():
        v = (chans or {}).get("signup")
        if str(v).isdigit():
            ids.append((f"Anmeldung {pool}", int(v)))
    if str(cfg.get("pug_channel_id") or "").isdigit():
        ids.append(("PUG-Anmeldung", int(cfg["pug_channel_id"])))
    for label, cid in ids:
        ch = guild.get_channel(cid)
        if ch is None:
            out.append(f"{label}: Kanal fehlt")
            continue
        p = ch.permissions_for(me)
        if not (p.view_channel and p.send_messages and p.embed_links):
            out.append(f"{label} (#{ch.name}): Bot darf nicht posten (ansehen/senden/Links einbetten)")
    # 2) Offiziers-Bereich nie für alle sichtbar
    off = _cat(guild, OFFICER_CATEGORY)
    if off is not None:
        for item in [off] + list(getattr(off, "channels", []) or []):
            if item.overwrites_for(everyone).view_channel is not False:
                out.append(f"{OFFICER_CATEGORY} / {item.name}: für @everyone sichtbar")
    # 3) Addon-Kanäle nie für Fremde/Gäste
    add = _cat(guild, ADDON_CATEGORY)
    guest = next((r for r in guild.roles if _fold(r.name) == "gast"), None)
    if add is not None:
        for item in [add] + list(getattr(add, "channels", []) or []):
            if item.overwrites_for(everyone).view_channel is not False:
                out.append(f"{ADDON_CATEGORY} / {item.name}: für @everyone sichtbar")
            if guest is not None and item.overwrites_for(guest).view_channel is True:
                out.append(f"{ADDON_CATEGORY} / {item.name}: für Gast sichtbar")
    # 4) Mitglieder-Bereich (falls eingerichtet) dicht, Rolle und #bewerbung vorhanden
    if cfg.get("member_area"):
        if not any(_fold(r.name) == _fold(member_area.MEMBER_ROLE) for r in guild.roles):
            out.append("Rolle Mitglied fehlt")
        if not any(_fold(c.name) == member_area.APPLY_CHANNEL for c in guild.text_channels):
            out.append("#bewerbung fehlt")
        for item in member_area.plan_items(guild):
            out.append(f"{getattr(item, 'name', '?')}: für @everyone sichtbar, gehört in den Mitglieder-Bereich")
    return out
