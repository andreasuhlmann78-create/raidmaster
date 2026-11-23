"""T-D-MITGL1: Kanäle der Gildenmitglieder (Auftrag D-MITGL1, ab Bot 1.5.189) – ohne Netz, mit nachgebautem Server.

In 💬 ALLGEMEIN: #mitglieder-chat, #offtopic, 🔊 Gildenhalle, 🔊 Offtopic-Talk. Rechte je Rolle: @everyone sieht nichts;
Mitglied/Raider/Gast lesen, schreiben, sprechen, verwalten nichts; Raidleitung/Offizier zusätzlich Nachrichten verwalten,
in Sprache auch Kanal verwalten, stummschalten, taub schalten, verschieben; der Bot hat je Kanal genau die Rechte des
Gildenchefs. Erster Lauf legt an, zweiter Lauf ändert nichts; vorhandene Kanäle (auch 🔊 Gildenhalle) werden übernommen,
#Allgemein bleibt unberührt; Gast wird dort nicht ausgeblendet; fehlen dem Bot Server-Rechte -> nichts ändern, melden;
Rollen über dem Bot werden gemeldet. #Allgemein steht nicht mehr auf der Liste zum Entfernen.
"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import discord  # noqa: E402

import server_setup as ss  # noqa: E402


class Rolle:
    def __init__(self, name, pos):
        self.name, self.position, self.id = name, pos, 1000 + pos

    def __hash__(self):
        return self.id

    def __eq__(self, o):
        return isinstance(o, Rolle) and o.id == self.id


class Kanal:
    def __init__(self, guild, name, kind, category=None, overwrites=None, topic=None):
        self.guild, self.name, self.kind, self.topic = guild, name, kind, topic
        self.category_id = category.id if category else None
        self.id = len(guild.calls) + 500 + len(guild.text_channels) + len(guild.voice_channels)
        self.overwrites = dict(overwrites or {})
        self.position, self.user_limit = 0, 0

    def overwrites_for(self, target):
        return self.overwrites.get(target, discord.PermissionOverwrite())

    async def set_permissions(self, target, overwrite=None, reason=None, **kw):
        self.guild.calls.append(("set", self.name, getattr(target, "name", "?")))
        self.overwrites[target] = overwrite if overwrite is not None else discord.PermissionOverwrite(**kw)

    async def edit(self, **kw):
        self.guild.calls.append(("edit", self.name))


class Server:
    def __init__(self, perms=None, bot_pos=10):
        self.calls = []
        self.roles = [Rolle("@everyone", 0), Rolle("Gast", 1), Rolle("Mitglied", 2), Rolle("Raider", 3),
                      Rolle("Raidleitung", 4), Rolle("Offizier", 5)]
        self.default_role = self.roles[0]
        bot_role = Rolle("RaidMaster", bot_pos)
        self.roles.append(bot_role)
        gp = perms if perms is not None else discord.Permissions(**{p: True for p in set(ss.LEADER_TEXT) | set(ss.LEADER_VOICE)})
        self.me = type("Me", (), {"guild_permissions": gp, "top_role": bot_role, "name": "RaidMaster", "id": 1,
                                  "__hash__": lambda s: 1, "__eq__": lambda s, o: o is s})()
        self.categories, self.text_channels, self.voice_channels = [], [], []
        allgemein = self._cat("💬 ALLGEMEIN")
        self.text_channels.append(Kanal(self, "Allgemein", "text", allgemein))   # vom Nutzer, begrenzt

    def _cat(self, name):
        c = type("Cat", (), {})()
        c.name, c.id, c.position = name, 100 + len(self.categories), len(self.categories)
        c.overwrites_for = lambda t: discord.PermissionOverwrite()

        async def setp(target, **kw):
            self.calls.append(("set", name, getattr(target, "name", "?")))
        c.set_permissions = setp
        self.categories.append(c)
        return c

    async def create_category(self, name, **kw):
        self.calls.append(("create_category", name))
        return self._cat(name)

    async def create_text_channel(self, name, category=None, overwrites=None, topic=None, **kw):
        self.calls.append(("create_text", name))
        ch = Kanal(self, name, "text", category, overwrites, topic)
        self.text_channels.append(ch)
        return ch

    async def create_voice_channel(self, name, category=None, overwrites=None, **kw):
        self.calls.append(("create_voice", name))
        ch = Kanal(self, name, "voice", category, overwrites)
        self.voice_channels.append(ch)
        return ch

    def role(self, name):
        return next(r for r in self.roles if r.name == name)

    def ch(self, name):
        return next(c for c in self.text_channels + self.voice_channels if c.name == name)


def run(g):
    return asyncio.run(ss.ensure_member_channels(g))


class Kanaele(unittest.TestCase):
    def test_anlegen_rechte_je_rolle(self):
        g = Server()
        rep = run(g)
        self.assertEqual(sorted(c[1] for c in g.calls if c[0] in ("create_text", "create_voice")),
                         ["Gildenhalle", "Offtopic-Talk", "mitglieder-chat", "offtopic"])
        self.assertTrue(all(r.startswith(("✅", "•", "🔐")) for r in rep), rep)
        for name, voice in (("mitglieder-chat", False), ("offtopic", False), ("Gildenhalle", True), ("Offtopic-Talk", True)):
            c = g.ch(name)
            self.assertEqual(c.category_id, g.categories[0].id, name)                 # in 💬 ALLGEMEIN
            ev = c.overwrites_for(g.default_role)
            self.assertIs(ev.view_channel, False, name)
            for r in ("Mitglied", "Raider", "Gast"):
                o = c.overwrites_for(g.role(r))
                self.assertTrue(o.view_channel and o.send_messages, (name, r))
                self.assertIsNone(o.manage_messages, (name, r))
                self.assertIsNone(getattr(o, "pin_messages", None), (name, r))
                self.assertIsNone(o.manage_channels, (name, r))
                if voice:
                    self.assertTrue(o.connect and o.speak, (name, r))
                    self.assertIsNone(o.mute_members, (name, r))
            for r in ("Raidleitung", "Offizier"):
                o = c.overwrites_for(g.role(r))
                self.assertTrue(o.view_channel and o.send_messages and o.manage_messages, (name, r))
                if hasattr(discord.Permissions, "pin_messages"):                # ab 1.5.190: Anheften ist eigenes Recht
                    self.assertTrue(o.pin_messages, (name, r))
                if voice:
                    self.assertTrue(o.connect and o.speak and o.mute_members and o.deafen_members and o.move_members
                                    and o.manage_channels, (name, r))
            # Bot = Gildenchef je Kanal (Nutzer 09:20)
            self.assertEqual(c.overwrites_for(g.me), discord.PermissionOverwrite(**(ss.LEADER_VOICE if voice else ss.LEADER_TEXT)))
        self.assertEqual(g.ch("Allgemein").overwrites, {})                              # #Allgemein unberührt
        self.assertEqual(g.ch("mitglieder-chat").topic, "Für alle Gildenmitglieder")

    def test_gildenchef_rechte_vollstaendig(self):
        """Nachtrag 09:20: sehen, schreiben, Nachrichten verwalten/anheften, Kanal verwalten (Name, Thema, Rechte),
        sprechen, stummschalten, taub schalten, verschieben – unabhängig von der Konstante geprüft."""
        text = {"view_channel", "send_messages", "read_message_history", "manage_messages", "manage_channels", "manage_roles"}
        if hasattr(discord.Permissions, "pin_messages"):
            text.add("pin_messages")
        voice = text | {"connect", "speak", "mute_members", "deafen_members", "move_members"}
        self.assertTrue(text <= {k for k, v in ss.LEADER_TEXT.items() if v})
        self.assertTrue(voice <= {k for k, v in ss.LEADER_VOICE.items() if v})

    def test_zweiter_lauf_aendert_nichts(self):
        g = Server()
        run(g)
        g.calls.clear()
        self.assertEqual(run(g), [])
        self.assertEqual(g.calls, [])
        self.assertEqual(len(g.text_channels) + len(g.voice_channels), 5)

    def test_vorhandene_uebernommen(self):
        g = Server()
        alt = Kanal(g, "Gildenhalle", "voice", g.categories[0])
        g.voice_channels.append(alt)
        run(g)
        self.assertEqual([c for c in g.voice_channels if c.name == "Gildenhalle"], [alt])  # nicht doppelt
        self.assertNotIn(("create_voice", "Gildenhalle"), g.calls)
        self.assertIs(alt.overwrites_for(g.default_role).view_channel, False)
        self.assertNotIn(("set", "Allgemein"), [c[:2] for c in g.calls])

    def test_fehlende_bot_rechte(self):
        g = Server(perms=discord.Permissions(view_channel=True, send_messages=True, manage_channels=True))
        rep = run(g)
        self.assertEqual(len(rep), 1)
        self.assertIn("dem Bot fehlen Server-Rechte", rep[0])
        self.assertIn("manage_roles", rep[0])
        self.assertEqual(g.calls, [])                                                   # nichts geändert
        g2 = Server(perms=discord.Permissions(administrator=True))
        self.assertTrue(any(c[0] == "create_text" for c in (run(g2) and g2.calls)))

    def test_rollen_ueber_dem_bot(self):
        g = Server(bot_pos=4)                                                            # unter Raidleitung/Offizier
        rep = run(g)
        self.assertIn("Rollen über dem Bot: Raidleitung, Offizier", rep[-1])
        self.assertIn("nicht vergeben oder entziehen", rep[-1])
        self.assertNotIn("stummschalten", rep[-1])

    def test_gast_nicht_ausgeblendet(self):
        g = Server()
        run(g)
        cat_def = next(c for c in ss.BASE_BOTTOM if c["name"] == ss.GENERAL)
        created = {c.name: c for c in g.text_channels + g.voice_channels}
        asyncio.run(ss._hide_from_guests(g, cat_def, {"Gast": g.role("Gast")}, created, [], "t"))
        for n in ss.MEMBER_CHANNELS:
            self.assertTrue(g.ch(n).overwrites_for(g.role("Gast")).view_channel, n)

    def test_allgemein_bleibt(self):
        from bot_harness import load_bot
        load_bot()
        self.assertNotIn("allgemein", sys.modules["kanalpflege_bot"].UNUSED_CHANNELS)


if __name__ == "__main__":
    unittest.main()
