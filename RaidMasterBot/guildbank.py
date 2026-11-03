"""Gildenbank im Discord: ein Kanal #gildenbank (Kategorie 🏦 GILDENBANK).

Oben stehen die Regeln aus guild_rules.json, darunter der Bestand vom Bank-Charakter. Den Bestand liest RaidMaster
(RaidMasterDB.bank) oder GuildSentinel (GuildSentinelDB.bank, gleiches Format); der Uploader schickt beide Dateien mit.
Der frühere Kanal #gildenbank-bestand wird aufgelöst: Bestand nach #gildenbank, Kanal löschen – aber nur, wenn darin
ausschliesslich Nachrichten des Bots stehen (sonst Meldung, einmal).

Die Funktionen arbeiten mit Discord-Objekten (Kanäle, Nachrichten) und einem Zustand (state.data als dict). Sie
kennen den Bot selbst nicht und lassen sich deshalb offline mit nachgebauten Kanälen testen (tests/test_guildbank.py).
"""
from __future__ import annotations

import discord

BANK_CHANNEL = "gildenbank"
OLD_BANK_CHANNEL = "gildenbank-bestand"
OLD_HISTORY_LIMIT = 200

OLD_HAS_MEMBER_MESSAGES = ("⚠️ #gildenbank-bestand enthält Nachrichten von Mitgliedern – bitte von Hand löschen. "
                           "Der Bestand steht ab jetzt unten in #gildenbank.")
OLD_DELETED = "🏦 #gildenbank-bestand gelöscht – der Bestand steht jetzt unten in #gildenbank."


def find_channel(channels, name: str):
    for ch in channels or []:
        if getattr(ch, "name", None) == name:
            return ch
    return None


async def _delete_messages(ch, ids) -> None:
    if ch is None:
        return
    for mid in ids or []:
        try:
            await ch.get_partial_message(int(mid)).delete()
        except discord.HTTPException:
            pass


async def reset_bank(ch, state: dict) -> None:
    """Bestands-Nachrichten im Kanal ch löschen und den Stand vergessen (wird beim nächsten Mal neu gepostet)."""
    await _delete_messages(ch, state.get("bank_messages"))
    state["bank_messages"] = []
    state.pop("bank_t", None)
    state.pop("bank_src", None)


async def only_bot_messages(ch, bot_user_id: int, limit: int = OLD_HISTORY_LIMIT) -> bool:
    async for m in ch.history(limit=limit):
        author = getattr(m, "author", None)
        if author is None or int(getattr(author, "id", 0) or 0) != int(bot_user_id):
            return False
    return True


async def migrate_old_channel(guild_channels, bank_ch, state: dict, bot_user_id: int, prev_ch=None) -> list[str]:
    """prev_ch = Kanal, in dem die Bestands-Nachrichten bisher stehen (z. B. #gildenbank-bestand).
    Ist das nicht #gildenbank, dort löschen und den Stand vergessen (der Bestand kommt neu unter die Regeln).
    #gildenbank-bestand danach einmal zu löschen versuchen. Liefert Meldungen für Log und #bot-log."""
    report: list[str] = []
    old = find_channel(guild_channels, OLD_BANK_CHANNEL)
    if prev_ch is None and state.get("bank_messages") and old is not None and old.id != bank_ch.id:
        prev_ch = old                              # Stand vor 1.5.96: Bestand lag in #gildenbank-bestand
    if prev_ch is not None and getattr(prev_ch, "id", None) != bank_ch.id:
        await reset_bank(prev_ch, state)
    if old is None or old.id == bank_ch.id or state.get("bank_old_checked"):
        return report
    state["bank_old_checked"] = True              # nur einmal versuchen, nicht bei jedem Start
    try:
        if await only_bot_messages(old, bot_user_id):
            await old.delete(reason="Gildenbank: Bestand steht jetzt in #gildenbank")
            report.append(OLD_DELETED)
        else:
            report.append(OLD_HAS_MEMBER_MESSAGES)
    except discord.HTTPException as e:
        report.append(f"⚠️ #gildenbank-bestand konnte nicht gelöscht werden ({e}) – bitte von Hand löschen.")
    return report


async def write_bank(ch, chunks: list[str], state: dict) -> None:
    """Bestand schreiben: vorhandene Bestands-Nachrichten bearbeiten (kein Neu-Posten), fehlende anhängen,
    überzählige löschen."""
    ids = list(state.get("bank_messages") or [])
    new_ids = []
    for i, text in enumerate(chunks):
        done = False
        if i < len(ids):
            try:
                await ch.get_partial_message(int(ids[i])).edit(content=text)
                new_ids.append(ids[i])
                done = True
            except discord.HTTPException:
                pass
        if not done:
            m = await ch.send(text)
            new_ids.append(m.id)
    for mid in ids[len(chunks):]:
        try:
            await ch.get_partial_message(int(mid)).delete()
        except discord.HTTPException:
            pass
    state["bank_messages"] = new_ids
    state["bank_channel"] = ch.id
