"""Offline-Test (Bot 1.5.99): noch nicht spielbare Raids ausblenden/einblenden, Kategorie-Reihenfolge, AFK.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import discord  # noqa: E402
import server_setup  # noqa: E402


class FakeTarget:
    def __init__(self, cid, name, overwrites=None, category_id=None):
        self.id, self.name, self.category_id = cid, name, category_id
        self.ow = dict(overwrites or {})
        self.calls = []

    def overwrites_for(self, who):
        o = self.ow.get(who)
        return discord.PermissionOverwrite(**{k: v for k, v in o}) if o else discord.PermissionOverwrite()

    async def set_permissions(self, who, overwrite=None, reason=None):
        self.calls.append(who)
        if overwrite is None:
            self.ow.pop(who, None)
        else:
            self.ow[who] = overwrite

    async def edit(self, category=None, **kw):
        self.category_id = category.id


class Named:
    def __init__(self, name, cid=0):
        self.name, self.id = name, cid


class FakeGuild:
    def __init__(self):
        self.default_role, self.me = Named("@everyone"), Named("bot")
        self.roles = [Named("Offizier")]
        self.categories, self.voice_channels, self.afk_channel = [], [], None


def run(coro):
    return asyncio.run(coro)


class RaidReleased(unittest.TestCase):
    def test_forever_und_freigeschaltet(self):
        self.assertTrue(server_setup.raid_released("mc", {}))
        self.assertTrue(server_setup.raid_released("hyjal", {}))
        self.assertFalse(server_setup.raid_released("bwl", {}))
        self.assertTrue(server_setup.raid_released("bwl", {"raids_unlocked": ["bwl"]}))
        self.assertTrue(server_setup.raid_released("bwl", {"hide_unreleased_raids": False}))
        self.assertTrue(server_setup.raid_released("i409", {}))     # automatisch erkannter Raid: immer sichtbar


class HideShow(unittest.TestCase):
    def setUp(self):
        self.g = FakeGuild()
        self.officer = self.g.roles[0]
        self.cat = FakeTarget(1, "🖤 PECHSCHWINGENHORT")
        self.sign = FakeTarget(2, "bwl-anmeldung")
        # readonly-Kanal: hat schon eigene Rechte für @everyone (send_messages=False) und den Bot
        self.tact = FakeTarget(3, "bwl-taktik", {self.g.default_role: discord.PermissionOverwrite(send_messages=False)})
        self.afk = FakeTarget(4, "AFK")
        self.cat.channels = [self.sign, self.tact, self.afk]

    def test_targets_ohne_fremde_kanaele(self):
        t = server_setup.raid_targets(self.cat, "bwl", [2])
        self.assertEqual([x.id for x in t], [1, 2, 3])            # AFK bleibt unberührt

    def test_ausblenden_und_genau_zurueck(self):
        targets = server_setup.raid_targets(self.cat, "bwl", [2, 3])
        prev = run(server_setup.hide_raid(self.g, targets, "t"))
        for t in targets:
            self.assertIs(t.overwrites_for(self.g.default_role).view_channel, False)
            self.assertIs(t.overwrites_for(self.g.me).view_channel, True)       # Bot sieht weiter alles
            self.assertIs(t.overwrites_for(self.officer).view_channel, True)    # Offiziere auch
        self.assertIs(self.tact.overwrites_for(self.g.default_role).send_messages, False)   # Rest bleibt
        run(server_setup.show_raid(self.g, targets, prev, "t"))
        self.assertNotIn(self.g.default_role, self.sign.ow)                       # wie vorher: kein Eintrag
        ow = self.tact.overwrites_for(self.g.default_role)
        self.assertIsNone(ow.view_channel)
        self.assertIs(ow.send_messages, False)

    def test_zweimal_ausblenden_aendert_nichts(self):
        targets = server_setup.raid_targets(self.cat, "bwl", [])
        run(server_setup.hide_raid(self.g, targets, "t"))
        n = len(self.sign.calls)
        run(server_setup.hide_raid(self.g, targets, "t"))
        self.assertEqual(len(self.sign.calls), n)


class Layout(unittest.TestCase):
    def test_gildenbank_unter_dungeons(self):
        self.assertEqual(server_setup.RULE_CATEGORY_PLACE["🏦 GILDENBANK"], server_setup.DUNGEONS)
        dungeons = next(c for c in server_setup.BASE_BOTTOM if c["name"] == server_setup.DUNGEONS)
        self.assertEqual(dungeons["after"], server_setup.GENERAL)  # also keine zwei Kategorien am selben Platz

    def test_keine_sprache_kategorie_afk_in_allgemein(self):
        names = [c["name"] for c in server_setup.BASE_TOP + server_setup.BASE_BOTTOM]
        self.assertNotIn("🔊 SPRACHE", names)
        general = next(c for c in server_setup.BASE_BOTTOM if c["name"] == server_setup.GENERAL)
        self.assertIn(("voice", "AFK", None, None), general["channels"])

    def test_afk_verschieben(self):
        g = FakeGuild()
        general = Named(server_setup.GENERAL, 50)
        g.categories = [general]
        afk = FakeTarget(7, "AFK", category_id=99)
        g.voice_channels = [afk]
        self.assertTrue(run(server_setup.move_afk_to_general(g)))
        self.assertEqual(afk.category_id, 50)
        self.assertEqual(run(server_setup.move_afk_to_general(g)), [])   # schon dort: nichts tun


if __name__ == "__main__":
    unittest.main()
