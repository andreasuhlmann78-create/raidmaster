"""Offline-Tests Bot 1.5.111: #testberichte aufräumen – nur abgeholte Nachrichten, nur dort, älter als 1 Stunde.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_DIR)
import discord  # noqa: E402
import tb_aufraeumen as tb  # noqa: E402

NOW = 1794200000.0


def snowflake(ts: float, n: int = 0) -> str:
    return str(((int(ts * 1000) - tb.DISCORD_EPOCH_MS) << 22) + n)


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class Partial:
    def __init__(self, ch, mid):
        self.ch, self.id = ch, mid

    async def delete(self):
        if self.id not in self.ch.msgs:
            raise discord.NotFound(Obj(status=404, reason="Not Found"), "Unknown Message")
        self.ch.msgs.remove(self.id)
        self.ch.deleted.append(self.id)


class Channel:
    def __init__(self, name, msgs=(), manage=True):
        self.name, self.msgs, self.deleted, self.manage = name, set(msgs), [], manage

    def permissions_for(self, member):
        return Obj(manage_messages=self.manage)

    def get_partial_message(self, mid):
        return Partial(self, str(mid))


def run(c):
    return asyncio.run(c)


class Aufraeumen(unittest.TestCase):
    def setUp(self):
        self.old = [snowflake(NOW - 7200, i) for i in range(3)]          # 2 Stunden alt
        self.young = snowflake(NOW - 600)                                  # 10 Minuten alt
        self.other = snowflake(NOW - 7200, 9)                              # Nachricht in einem anderen Kanal
        self.tb = Channel("testberichte", self.old + [self.young, snowflake(NOW - 9000, 5)])
        self.gen = Channel("allgemein", [self.other])
        self.guild = Obj(text_channels=[self.gen, self.tb], me=Obj())

    def test_t01_nur_abgeholte_und_alte(self):
        ids = self.old + [self.young]
        done = []
        n, note = run(tb.cleanup(self.guild, ids, done, now=NOW))
        self.assertEqual(n, 3)
        self.assertIsNone(note)
        self.assertEqual(sorted(self.tb.deleted), sorted(self.old))
        self.assertIn(self.young, self.tb.msgs)                            # jünger als 1 Stunde bleibt
        self.assertIn(snowflake(NOW - 9000, 5), self.tb.msgs)             # nicht abgeholt bleibt

    def test_t02_nie_andere_kanaele(self):
        done = []
        run(tb.cleanup(self.guild, [self.other], done, now=NOW))
        self.assertEqual(self.gen.deleted, [])
        self.assertIn(self.other, self.gen.msgs)
        self.assertEqual(done, [self.other])                               # nicht gefunden: nie wieder versuchen
        # nur der Kanal, der genau "testberichte" heisst
        g = Obj(text_channels=[Channel("testberichte-alt", self.old)], me=Obj())
        self.assertEqual(run(tb.cleanup(g, self.old, [], now=NOW)), (0, None))

    def test_t03_erledigte_nicht_nochmals(self):
        done = []
        run(tb.cleanup(self.guild, self.old, done, now=NOW))
        self.tb.deleted.clear()
        n, _ = run(tb.cleanup(self.guild, self.old, done, now=NOW))
        self.assertEqual((n, self.tb.deleted), (0, []))

    def test_t04_ohne_recht_nur_hinweis(self):
        self.tb.manage = False
        n, note = run(tb.cleanup(self.guild, self.old, [], now=NOW))
        self.assertEqual(n, 0)
        self.assertIn("Nachrichten verwalten", note)
        self.assertEqual(self.tb.deleted, [])

    def test_t05_ids_aus_der_datei(self):
        text = '{"ids": ["1569227090916679724", "abc", 12, "1"]}'
        self.assertEqual(tb.parse_ids(text), ["1569227090916679724"])
        self.assertEqual(tb.parse_ids("kaputt"), [])
        self.assertEqual(tb.parse_ids('["1569227090916679724"]'), [])
        self.assertEqual(tb.raw_url("besitzer/repo"),
                         "https://raw.githubusercontent.com/besitzer/repo/HEAD/testberichte/abgeholt.json")

    def test_t06_grenze_je_durchgang(self):
        many = [snowflake(NOW - 7200, i) for i in range(150)]
        ch = Channel("testberichte", many)
        g = Obj(text_channels=[ch], me=Obj())
        n, _ = run(tb.cleanup(g, many, [], now=NOW))
        self.assertEqual(n, tb.MAX_PER_RUN)

    def test_t07_bot_postet_nichts(self):
        with open(os.path.join(BOT_DIR, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def tb_cleanup_loop"):src.index("async def before_tb_cleanup")]
        self.assertNotIn(".send(", body)
        self.assertIn("tb_aufraeumen.cleanup", body)
        with open(os.path.join(BOT_DIR, "tb_aufraeumen.py"), encoding="utf-8") as f:
            mod = f.read()
        self.assertNotIn(".send(", mod)
        self.assertNotIn("purge", mod)
        self.assertNotIn("history(", mod)


if __name__ == "__main__":
    unittest.main()
