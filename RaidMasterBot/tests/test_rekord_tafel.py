"""T-RT: Rekord-Tafeln der Ruhmeshalle (ab Bot 1.5.136) – Zuordnung, Bestzeiten, ganzer Raid, Text, Ablauf im Bot."""
import asyncio
import os
import subprocess
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import rekord_tafel as rt  # noqa: E402

RAIDS = [
    {"key": "mc", "bosses": [{"e": [663], "n": "Lucifron"}, {"e": [664], "n": "Magmadar"}, {"e": [672], "n": "Ragnaros"}]},
    {"key": "ony", "bosses": [{"e": [1084], "n": "Onyxia"}]},
    {"key": "barrow", "bosses": []},
]
NAMES = {"mc": "Molten Core", "ony": "Onyxias Hort", "barrow": "Barrow Deeps"}
DAY = 86400
T0 = 1_762_000_000


def k(e, t, d, p="mc", n=None):
    return {"e": e, "t": t, "d": d, "p": p, "n": n or f"Boss {e}"}


class Zuordnung(unittest.TestCase):
    def test_encounter_vor_topf(self):
        em = rt.encounter_map(RAIDS)
        self.assertEqual(rt.raid_of(k(1084, 1, 60, p="mc"), em, RAIDS), "ony")      # Topf falsch, ID gewinnt
        self.assertEqual(rt.raid_of(k(9001, 1, 60, p="barrow"), em, RAIDS), "barrow")  # eigener Raid ohne Liste
        self.assertEqual(rt.raid_of(k(2000, 1, 60, p="mc"), em, RAIDS), rt.OTHER)     # Dungeon-Boss am MC-Abend
        self.assertEqual(rt.raid_of(k(2000, 1, 60, p=None), em, RAIDS), rt.OTHER)

    def test_bosses_json_aktuell_und_forever(self):
        raids = rt.load_bosses()
        keys = [r["key"] for r in raids]
        self.assertEqual(keys[:4], ["mc", "barrow", "hyjal", "ony"])
        mc = raids[0]["bosses"]
        self.assertEqual((mc[0]["n"], mc[0]["e"], mc[-1]["n"], len(mc)), ("Lucifron", [663], "Ragnaros", 10))
        self.assertNotIn("kara", keys)                                                # nur Raids von WoW Forever
        naxx = next(r for r in raids if r["key"] == "naxx")
        self.assertEqual(len(naxx["bosses"]), 15)                                     # Classic, nicht Wotlk
        repo_addon = os.path.join(os.path.dirname(__file__), "..", "..", "RaidMaster", "Data.lua")
        if os.path.exists(repo_addon):                                                # im Repo: nie veraltet
            r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "make_bosses.py"),
                                "--check"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_kaputte_datei(self):
        self.assertEqual(rt.load_bosses("/gibt/es/nicht.json"), [])


class Tafeln(unittest.TestCase):
    def kills(self):
        return [
            # Abend 1: ganzer MC (Lucifron 1:35, Magmadar 2:00, Ragnaros 3:00), Beginn = 1000 - 95
            k(663, T0 + 1000, 95), k(664, T0 + 2000, 120), k(672, T0 + 5000, 180),
            # Abend 2 (eine Woche später): Lucifron schneller (1:12), Magmadar langsamer, kein Ragnaros
            k(663, T0 + 7 * DAY + 1000, 72), k(664, T0 + 7 * DAY + 2000, 130),
            # Onyxia an Abend 2, mit falschem Topf
            k(1084, T0 + 7 * DAY + 3000, 185, p="mc"),
            # Dungeon-Boss, Messfehler 5 s (zählt nicht als Bestzeit)
            k(2000, T0 + 7 * DAY + 100, 5, n="Rhahk'Zor"),
            # Barrow: zwei unbekannte Bosse, Reihenfolge des ersten Kills
            k(9002, T0 + 2 * DAY, 300, p="barrow", n="Zweiter"), k(9001, T0 + 2 * DAY - 600, 200, p="barrow", n="Erster"),
        ]

    def test_reihenfolge_und_werte(self):
        b = rt.boards(self.kills(), RAIDS, NAMES)
        self.assertEqual([x["key"] for x in b], ["mc", "ony", "barrow", rt.OTHER])
        mc = b[0]
        self.assertEqual(mc["title"], "⏱️ Rekorde · Molten Core")
        self.assertEqual([r["n"] for r in mc["rows"]], ["Lucifron", "Magmadar", "Ragnaros"])
        luc, mag, rag = mc["rows"]
        self.assertEqual((luc["d"], luc["new"]), (72, True))                         # neu am letzten Abend
        self.assertEqual((mag["d"], mag["new"]), (120, False))                      # alter Rekord bleibt
        self.assertEqual((rag["d"], rag["new"]), (180, False))
        # ganzer Raid: 5000 - (1000 - 95) = 4095 s
        self.assertEqual(mc["full"], {"d": 4095, "t": T0 + 5000})
        self.assertEqual([r["n"] for r in b[2]["rows"]], ["Erster", "Zweiter"])
        other = b[3]
        self.assertEqual(other["title"], "⏱️ Rekorde · Weitere Bosse (Dungeons und andere)")
        self.assertEqual((other["rows"][0]["d"], other["rows"][0]["killed"]), (None, True))

    def test_text(self):
        b = rt.boards(self.kills(), RAIDS, NAMES)
        t = rt.board_text(b[0])
        self.assertIn(f"**Lucifron** – **1:12** 🆕 · <t:{T0 + 7 * DAY + 1000}:d>", t)
        self.assertIn(f"**Magmadar** – **2:00** · <t:{T0 + 2000}:d>", t)
        self.assertIn("🏁 Ganzer Raid (erster Pull bis letzter Boss): **1:08:15**", t)
        self.assertIn("gelegt, keine Kampfdauer gemessen", rt.board_text(b[3]))
        self.assertLessEqual(len(t), 4000)

    def test_ohne_kill_und_ohne_dauer(self):
        b = rt.boards([k(663, T0, 95)], RAIDS, NAMES)
        self.assertEqual(len(b), 1)                                                   # nur Raids mit Kill
        self.assertIn("Ragnaros – noch kein Kill", rt.board_text(b[0]))
        self.assertIsNone(b[0]["full"])
        # alle Bosse, aber erster Kill ohne Dauer -> Beginn unbekannt -> kein ganzer Raid
        ks = [k(663, T0, None), k(664, T0 + 100, 60), k(672, T0 + 200, 60)]
        self.assertIsNone(rt.boards(ks, RAIDS, NAMES)[0]["full"])
        # Lücke > 6 h trennt Abende -> kein ganzer Raid
        ks = [k(663, T0, 60), k(664, T0 + 100, 60), k(672, T0 + 7 * 3600, 60)]
        self.assertIsNone(rt.boards(ks, RAIDS, NAMES)[0]["full"])
        self.assertEqual(rt.boards([], RAIDS, NAMES), [])
        self.assertEqual(rt.boards([{"e": None, "t": 1}], RAIDS, NAMES), [])

    def test_fmt_hash_altzeilen(self):
        self.assertEqual((rt.fmt(72), rt.fmt(4095), rt.fmt(None), rt.fmt(0)), ("1:12", "1:08:15", "–", "0:00"))
        b1 = rt.boards(self.kills(), RAIDS, NAMES)[0]
        b2 = rt.boards(self.kills(), RAIDS, NAMES)[0]
        self.assertEqual(rt.board_hash(b1), rt.board_hash(b2))
        b3 = rt.boards(self.kills() + [k(664, T0 + 7 * DAY + 2500, 99)], RAIDS, NAMES)[0]
        self.assertNotEqual(rt.board_hash(b1), rt.board_hash(b3))
        self.assertTrue(rt.is_old_record_line("⏱️ **Neuer Rekord: Lucifron in 1:12** (vorher 1:35 …"))
        for no in ("🏆 Erstkill", "", None, "⏱️ Rekorde · Molten Core"):
            self.assertFalse(rt.is_old_record_line(no))


class Msg:
    _next = 100

    def __init__(self, ch, content=None, embed=None, author=1):
        Msg._next += 1
        self.id, self.ch, self.content, self.embed = Msg._next, ch, content, embed
        self.author = types.SimpleNamespace(id=author)

    async def edit(self, embed=None, **kw):
        self.embed = embed
        self.ch.edits += 1

    async def delete(self):
        self.ch.msgs.remove(self)


class Chan:
    def __init__(self):
        self.msgs, self.edits = [], 0

    async def send(self, content=None, embed=None, **kw):
        m = Msg(self, content, embed)
        self.msgs.append(m)
        return m

    async def fetch_message(self, mid):
        import discord
        for m in self.msgs:
            if m.id == mid:
                return m
        raise discord.NotFound(types.SimpleNamespace(status=404, reason="x"), "weg")

    def history(self, limit=100):
        msgs = list(reversed(self.msgs))[:limit]

        async def gen():
            for m in msgs:
                yield m
        return gen()


class BotAblauf(unittest.TestCase):
    """Mit dem echten bot.py (tests/bot_harness.py) und einem nachgebauten Kanal."""
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()

    def setUp(self):
        b = self.bot
        self.saved = (b.RECORD_BOSSES, dict(b.kills_db.data), dict(b.state.data), b.bot._connection.user)
        b.RECORD_BOSSES = RAIDS
        b.kills_db.data = {"kills": Tafeln().kills()}
        b.state.data.pop("record_boards", None)
        b.state.data.pop("record_lines_cleaned", None)
        b.bot._connection.user = types.SimpleNamespace(id=1)
        self._sleep = b.asyncio.sleep

        async def nosleep(_):
            return None
        b.asyncio.sleep = nosleep

    def tearDown(self):
        b = self.bot
        b.RECORD_BOSSES, b.kills_db.data = self.saved[0], self.saved[1]
        b.state.data.clear()
        b.state.data.update(self.saved[2])
        b.bot._connection.user = self.saved[3]
        b.asyncio.sleep = self._sleep

    def titles(self, ch):
        return [m.embed.title for m in ch.msgs if m.embed]

    def test_erst_posten_dann_nur_bearbeiten(self):
        ch = Chan()
        asyncio.run(ch.send("🏆 Erstkill … bleibt"))
        old = asyncio.run(ch.send("⏱️ **Neuer Rekord: Lucifron in 1:35** (vorher 2:00 …)"))
        fremd = Msg(ch, "⏱️ **Neuer Rekord: von jemand anderem", author=2)
        ch.msgs.append(fremd)
        r = asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual((r["posted"], r["deleted_old"]), (4, 1))
        self.assertNotIn(old, ch.msgs)                                    # alte Bot-Zeile weg
        self.assertIn(fremd, ch.msgs)                                     # fremde Nachricht bleibt
        self.assertEqual(ch.msgs[0].content, "🏆 Erstkill … bleibt")      # Erstkill bleibt
        self.assertEqual(self.titles(ch), ["⏱️ Rekorde · Molten Core", "⏱️ Rekorde · Onyxias Hort",
                                           "⏱️ Rekorde · Barrow Deeps",
                                           "⏱️ Rekorde · Weitere Bosse (Dungeons und andere)"])
        # nochmals ohne Änderung: nichts gepostet, nichts bearbeitet
        r = asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual((r["posted"], r["edited"], r["deleted_old"]), (0, 0, 0))
        # neuer Rekord Magmadar: nur die MC-Tafel wird bearbeitet, kein neuer Beitrag
        n = len(ch.msgs)
        self.bot.kills_db.data["kills"].append(k(664, T0 + 8 * DAY, 99))
        r = asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual((r["posted"], r["edited"]), (0, 1))
        self.assertEqual(len(ch.msgs), n)
        self.assertIn("**Magmadar** – **1:39** 🆕", ch.msgs[-4].embed.description)

    def test_neuer_raid_ordnet_neu(self):
        ch = Chan()
        self.bot.kills_db.data = {"kills": [k(663, T0, 95)]}
        asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual(self.titles(ch), ["⏱️ Rekorde · Molten Core"])
        asyncio.run(ch.send("🏆 Erstkill Onyxia"))
        self.bot.kills_db.data["kills"].append(k(1084, T0 + DAY, 185, p="ony"))
        r = asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual(r["posted"], 2)
        self.assertEqual(self.titles(ch), ["⏱️ Rekorde · Molten Core", "⏱️ Rekorde · Onyxias Hort"])
        self.assertEqual(len([m for m in ch.msgs if m.embed]), 2)        # nichts doppelt

    def test_tafel_von_hand_geloescht(self):
        ch = Chan()
        asyncio.run(self.bot.update_record_boards(ch))
        ch.msgs.remove(ch.msgs[0])                                        # jemand löscht die MC-Tafel
        self.bot.kills_db.data["kills"].append(k(663, T0 + 9 * DAY, 60))
        r = asyncio.run(self.bot.update_record_boards(ch))
        self.assertEqual(r["posted"], 4)
        self.assertEqual(len([m for m in ch.msgs if m.embed]), 4)


if __name__ == "__main__":
    unittest.main()
