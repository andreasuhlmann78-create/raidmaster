"""T-D-CHK1 (ab Bot 1.5.194, Auftrag Supervisor 24.11. 10:40) – ohne Netz.

EIN Ort für Reihe/Fassung (announce_reihe.py), den Bot UND die Discord-Prüfung (discord-check/check.py):
- Fassungen ohne Punkt-Version: "<name>.md" = 1, "<name>-N.md" = N; neueste je Reihe = grösste Fassung (am echten announce/ belegt:
  BuffSentinel -12, GuildSentinel -19, ThreatSentinel 2.2, LevelPilot-Übersicht 3.12.94).
- Bot: repair_missing_announcements gibt nie eine ältere Fassung frei (Vorfall 24.11. 10:28: -10 bis -18 freigegeben, 10:31 kurz neu
  gepostet); check_announcements postet keine ältere Fassung ohne Punkt-Version; eine neue Fassung wird gepostet.
- Teilung: Absatz > 1900 an Zeilen statt bei 2000 abgeschnitten; bei allen anderen Dateien gleiche Teile wie bisher.
- repair_truncated_announcements: nur die neueste Fassung, bearbeitet + hängt an, löscht nie, einmal je Version.
- check.py: prüft je Reihe nur die neueste, ältere/abgelöste nur zur Info.
"""
import asyncio
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ANN = os.path.join(ROOT, "announce")

import announce_reihe as ar  # noqa: E402


def md_files():
    return [f for f in os.listdir(ANN) if f.lower().endswith(".md")]


def read(fn):
    with open(os.path.join(ANN, fn), encoding="utf-8") as f:
        return f.read().strip()


class Reihe(unittest.TestCase):
    def test_fassung(self):
        self.assertEqual(ar.fassung("gs__gs-0-vorstellung.md"), ("gs__gs-0-vorstellung", (1,)))
        self.assertEqual(ar.fassung("gs__gs-0-vorstellung-19.md"), ("gs__gs-0-vorstellung", (19,)))
        self.assertEqual(ar.fassung("ts__ts-0-vorstellung-2.2.md"), ("ts__ts-0-vorstellung", (2, 2)))
        self.assertEqual(ar.fassung("raid-addon-zusammenfassung-3.0.0.md"), (None, None))
        self.assertEqual(ar.fassung("bild.png"), (None, None))
        # -19 neuer als -2 (Zahl, nicht Text) und als die Datei ohne Nummer
        self.assertEqual(ar.neueste(["a__x-2.md", "a__x-19.md", "a__x.md"])["a__x"][0], "a__x-19.md")
        self.assertEqual(ar.aeltere(["a__x-2.md", "a__x-19.md", "a__x.md"]), {"a__x-2.md": "a__x-19.md", "a__x.md": "a__x-19.md"})

    def test_echtes_announce_neueste(self):
        top = {fn for fn, _ in ar.neueste(md_files()).values()}
        for fn in ("buffsentinel__buffsentinel-0-vorstellung-12.md", "guildsentinel__guildsentinel-0-vorstellung-19.md",
                   "threatsentinel__threatsentinel-0-vorstellung-2.2.md", "levelpilot__levelpilot-uebersicht-3.12.94.md"):
            self.assertIn(fn, top)
        old = ar.aeltere(md_files())
        for fn in ("guildsentinel__guildsentinel-0-vorstellung-18.md", "guildsentinel__guildsentinel-0-vorstellung.md",
                   "buffsentinel__buffsentinel-0-vorstellung-11.md", "levelpilot__levelpilot-uebersicht.md",
                   "threatsentinel__threatsentinel-0-vorstellung.md"):
            self.assertIn(fn, old)

    def test_teilung_gleich_ausser_zu_langen_absaetzen(self):
        changed = []
        for fn in md_files():
            t = read(fn)
            new, old = ar.split_parts(t), ar.old_split(t)
            self.assertTrue(all(len(p) <= 1900 for p in new), fn)
            if any(len(p) > 1900 for p in old):             # bis 1.5.193 zu lang (über 2000: abgeschnitten)
                changed.append(fn)
            else:
                self.assertEqual(new, old, fn)          # sonst nichts geändert (keine unnötigen Bearbeitungen)
            joined = "\n".join(new)
            for ln in t.splitlines():
                self.assertIn(ln, joined, fn)           # nichts verloren
        self.assertIn("levelpilot__levelpilot-uebersicht-3.12.94.md", changed)
        self.assertTrue(all(fn.startswith("levelpilot__levelpilot-uebersicht-3.12.") for fn in changed), changed)

    def test_die_drei_fehlenden_zeilen(self):
        t = read("levelpilot__levelpilot-uebersicht-3.12.94.md")
        cut = "\n".join(p[:2000] for p in ar.old_split(t))
        new = "\n".join(ar.split_parts(t))
        for s in ("Pflichtregel: nie zu Zielen mit Mobs 3", "Auf WoW Forever eingestellt: Questlog mit 40 Plätzen"):
            self.assertNotIn(s, cut)                    # so fehlte es im Discord (Prüfung 24.11. 08:24)
            self.assertIn(s, new)

    def test_harte_teilung_einer_zeile(self):
        t = "Kopf\n\n" + "x" * 4500
        parts = ar.split_parts(t)
        self.assertEqual("".join(parts).replace("\n", ""), "Kopf" + "x" * 4500)
        self.assertTrue(all(len(p) <= 1900 for p in parts))


class Msg:
    def __init__(self, mid, content):
        self.id, self.content, self.edits = mid, content, 0

    async def edit(self, content=None, **kw):
        self.content, self.edits = content, self.edits + 1

    async def delete(self):
        raise AssertionError("es darf nichts gelöscht werden")


class Kanal:
    def __init__(self, msgs=(), missing=()):
        self.id = 7
        self.msgs = {m.id: m for m in msgs}
        self.missing = set(missing)
        self.sent = []

    async def fetch_message(self, mid):
        import discord
        if int(mid) in self.missing or int(mid) not in self.msgs:
            raise discord.NotFound(types.SimpleNamespace(status=404, reason="x"), "weg")
        return self.msgs[int(mid)]

    async def send(self, text=None, **kw):
        m = Msg(9000 + len(self.sent), text)
        self.sent.append(m)
        self.msgs[m.id] = m
        return m


class BotTeil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.b, _ = load_bot()
        cls.m = sys.modules["ankuendigung_bot"]

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        b, m = self.b, self.m
        self.saved_b = {k: getattr(b, k) for k in ("ANNOUNCE_DIR", "channel_by_id", "post_bot_log")}
        names = ("ANNOUNCE_DIR", "announce_target", "cleanup_announcements_once", "remove_deleted_announcements",
                 "resolve_announce_text", "remove_old_announcements", "remove_same_title", "post_bot_log", "channel_by_id")
        self.saved_m = {k: getattr(m, k) for k in names}
        keys = ("announced", "announce_msgs", "announce_old_skipped")
        self.saved_state = {k: m.state.data.get(k) for k in keys}
        self.saved_markers = [k for k in m.state.data if k.startswith(("announce_repaired_", "announce_truncfix_"))]
        self.saved_save = m.state.save
        m.state.save = lambda: None
        for k in self.saved_markers:
            m.state.data.pop(k, None)
        self.logs = []

        async def blog(t):
            self.logs.append(t)

        async def noop(*a, **k):
            return 0

        async def resolve(text):
            return text, []
        b.ANNOUNCE_DIR = m.ANNOUNCE_DIR = self.dir
        b.post_bot_log = m.post_bot_log = blog
        m.cleanup_announcements_once = m.remove_deleted_announcements = noop
        m.remove_old_announcements = m.remove_same_title = noop
        m.resolve_announce_text = resolve

    def tearDown(self):
        b, m = self.b, self.m
        for k, v in self.saved_b.items():
            setattr(b, k, v)
        for k, v in self.saved_m.items():
            setattr(m, k, v)
        for k, v in self.saved_state.items():
            if v is None:
                m.state.data.pop(k, None)
            else:
                m.state.data[k] = v
        for k in [k for k in m.state.data if k.startswith(("announce_repaired_", "announce_truncfix_"))]:
            m.state.data.pop(k, None)
        for k in self.saved_markers:
            m.state.data[k] = True
        m.state.save = self.saved_save
        shutil.rmtree(self.dir)

    def datei(self, name, text="🛡️ **GuildSentinel – das Gildentool**\nInhalt"):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_vorfall_10_28_nur_neueste_freigeben(self):
        """Nachgestellt: -10 … -19 gelten als gepostet, ihre Nachrichten sind weg (ersetzt). Nur -19 darf frei werden."""
        names = [f"guildsentinel__guildsentinel-0-vorstellung-{n}.md" for n in range(10, 20)]
        for i, n in enumerate(names):
            self.datei(n)
        ch = Kanal(missing=range(100, 120))

        async def by_id(cid):
            return ch
        self.b.channel_by_id = by_id
        st = self.m.state.data
        st["announced"] = list(names)
        st["announce_msgs"] = {n: {"ch": 7, "ids": [100 + i], "series": None, "ver": None} for i, n in enumerate(names)}
        asyncio.run(self.b.repair_missing_announcements())
        self.assertEqual(sorted(set(names) - set(st["announced"])), ["guildsentinel__guildsentinel-0-vorstellung-19.md"])
        self.assertIn("vorstellung-19.md", self.logs[0])
        self.assertNotIn("vorstellung-18.md", self.logs[0])

    def test_gegenprobe_ohne_regel_alle_frei(self):
        """Gegenprobe: ohne die Regel (aeltere leer) werden wie am 24.11. alle 10 frei."""
        names = [f"guildsentinel__guildsentinel-0-vorstellung-{n}.md" for n in range(10, 20)]
        for n in names:
            self.datei(n)
        ch = Kanal(missing=range(100, 120))

        async def by_id(cid):
            return ch
        self.b.channel_by_id = by_id
        st = self.m.state.data
        st["announced"] = list(names)
        st["announce_msgs"] = {n: {"ch": 7, "ids": [100 + i], "series": None, "ver": None} for i, n in enumerate(names)}
        orig = self.m.aeltere
        self.m.aeltere = lambda fns: {}
        try:
            asyncio.run(self.b.repair_missing_announcements())
        finally:
            self.m.aeltere = orig
        self.assertEqual(st["announced"], [])

    def test_aeltere_fassung_nie_posten_neue_schon(self):
        ch = Kanal()

        async def target(fn):
            return ch
        self.m.announce_target = target
        st = self.m.state.data
        st["announced"], st["announce_msgs"] = ["guildsentinel__guildsentinel-0-vorstellung-19.md"], {}
        st.pop("announce_old_skipped", None)
        self.datei("guildsentinel__guildsentinel-0-vorstellung-19.md")
        self.datei("guildsentinel__guildsentinel-0-vorstellung-18.md")      # nicht gepostet, ältere Fassung
        self.datei("guildsentinel__guildsentinel-0-vorstellung.md")
        asyncio.run(self.m.check_announcements())
        self.assertEqual(ch.sent, [])
        self.assertEqual(len(self.logs), 1)
        self.assertIn("• `guildsentinel__guildsentinel-0-vorstellung-18.md`: Fassung 18 ist nicht neuer", self.logs[0])
        asyncio.run(self.m.check_announcements())
        self.assertEqual(len(self.logs), 1)                                 # einmal melden
        self.datei("guildsentinel__guildsentinel-0-vorstellung-20.md")      # neue Fassung -> posten
        asyncio.run(self.m.check_announcements())
        self.assertEqual(len(ch.sent), 1)
        self.assertIn("guildsentinel__guildsentinel-0-vorstellung-20.md", st["announced"])

    def test_aeltere_neben_neuerer_auch_ohne_gepostete(self):
        """Beide nicht gepostet (z. B. neuer Server): nur die neueste Fassung."""
        ch = Kanal()

        async def target(fn):
            return ch
        self.m.announce_target = target
        st = self.m.state.data
        st["announced"], st["announce_msgs"] = [], {}
        st.pop("announce_old_skipped", None)
        self.datei("buffsentinel__buffsentinel-0-vorstellung-11.md")
        self.datei("buffsentinel__buffsentinel-0-vorstellung-12.md")
        asyncio.run(self.m.check_announcements())
        self.assertEqual(len(ch.sent), 1)
        self.assertEqual(st["announced"], ["buffsentinel__buffsentinel-0-vorstellung-12.md"])
        self.assertIn("neueste ist `buffsentinel__buffsentinel-0-vorstellung-12.md`", self.logs[0])

    def test_neuer_beitrag_mit_langem_absatz_vollstaendig(self):
        ch = Kanal()

        async def target(fn):
            return ch
        self.m.announce_target = target
        st = self.m.state.data
        st["announced"], st["announce_msgs"] = [], {}
        text = "📘 **Titel**\n\n" + "\n".join(f"• Zeile {i:03d} " + "y" * 60 for i in range(40))   # ein Absatz ~2900 Zeichen
        self.datei("levelpilot__neu-1.0.md", text)
        asyncio.run(self.m.check_announcements())
        self.assertGreater(len(ch.sent), 1)
        self.assertTrue(all(len(m.content) <= 1900 for m in ch.sent))
        joined = "\n".join(m.content for m in ch.sent)
        for ln in text.splitlines():
            self.assertIn(ln, joined)

    def lp_setup(self):
        fn = "levelpilot__levelpilot-uebersicht-3.12.94.md"
        text = read(fn)
        self.datei(fn, text)
        self.datei("levelpilot__levelpilot-uebersicht-3.12.93.md", read("levelpilot__levelpilot-uebersicht-3.12.93.md"))
        old = [p[:2000] for p in ar.old_split(text)]
        msgs = [Msg(200 + i, p) for i, p in enumerate(old)]
        ch = Kanal(msgs)

        async def by_id(cid):
            return ch
        self.m.channel_by_id = by_id
        st = self.m.state.data
        st["announce_msgs"] = {fn: {"ch": 7, "ids": [m.id for m in msgs], "series": "levelpilot__levelpilot-uebersicht",
                                    "ver": [3, 12, 94]},
                               "levelpilot__levelpilot-uebersicht-3.12.93.md": {"ch": 7, "ids": [1], "series": "x", "ver": [1]}}
        return fn, text, msgs, ch

    def test_abgeschnitten_vervollstaendigen(self):
        fn, text, msgs, ch = self.lp_setup()
        notes = asyncio.run(self.m.repair_truncated_announcements())
        new = ar.split_parts(text)
        self.assertEqual([m.content for m in msgs] + [m.content for m in ch.sent], new)
        self.assertEqual(len(ch.sent), len(new) - len(msgs))
        self.assertEqual(len(notes), 1)
        self.assertIn(f"`{fn}`", notes[0])
        self.assertEqual(self.m.state.data["announce_msgs"][fn]["ids"], [m.id for m in msgs] + [m.id for m in ch.sent])
        self.assertEqual(msgs[0].edits, 0)                                  # unveränderter Teil nicht angefasst
        self.assertEqual(asyncio.run(self.m.repair_truncated_announcements()), [])   # einmal je Version
        for k in [k for k in self.m.state.data if k.startswith("announce_truncfix_")]:
            self.m.state.data.pop(k)
        n_sent = len(ch.sent)
        self.assertEqual(asyncio.run(self.m.repair_truncated_announcements()), [])   # schon richtig: nichts mehr
        self.assertEqual(len(ch.sent), n_sent)

    def test_aeltere_fassung_nie_nachbessern(self):
        fn, text, msgs, ch = self.lp_setup()
        self.datei("levelpilot__levelpilot-uebersicht-3.12.95.md", text)    # jetzt gibt es eine neuere
        self.assertEqual(asyncio.run(self.m.repair_truncated_announcements()), [])
        self.assertEqual(sum(m.edits for m in msgs) + len(ch.sent), 0)

    def test_teil_fehlt_nicht_bearbeiten(self):
        fn, text, msgs, ch = self.lp_setup()
        ch.missing.add(msgs[2].id)
        notes = asyncio.run(self.m.repair_truncated_announcements())
        self.assertIn("nicht bearbeitet", notes[0])
        self.assertEqual(sum(m.edits for m in msgs) + len(ch.sent), 0)


class Pruefung(unittest.TestCase):
    def test_check_py_gleiche_regel(self):
        sys.path.insert(0, os.path.join(ROOT, "discord-check"))
        try:
            import check
        except ImportError as e:
            self.skipTest(f"check.py nicht ladbar: {e}")
        self.assertIs(check.announce_reihe, ar)
        fns = md_files()
        todo, info = check.select_announcements(fns)
        self.assertEqual(sorted(todo), sorted(fn for fn, _ in ar.neueste(fns).values()))
        self.assertIn("guildsentinel__guildsentinel-0-vorstellung-19.md", todo)
        self.assertNotIn("guildsentinel__guildsentinel-0-vorstellung-10.md", todo)
        why = dict(info)
        self.assertEqual(why["guildsentinel__guildsentinel-0-vorstellung-10.md"],
                         "ältere Fassung, neueste: guildsentinel__guildsentinel-0-vorstellung-19.md")
        self.assertIn("abgelöst", why["raid-addon-zusammenfassung-3.0.0.md"])
        self.assertNotIn("raid-addon-zusammenfassung-3.0.0.md", todo)
        self.assertNotIn("levelpilot__levelpilot-uebersicht-3.12.93.md", why)   # Punkt-Versionen still wie bisher
        # alle 26 "veraltet" vom 24.11. 08:24 ausser der echten Lücke (LevelPilot 3.12.94) sind nicht mehr zu prüfen
        for fn in [f"guildsentinel__guildsentinel-0-vorstellung-{n}.md" for n in (2, 3, 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18)] \
                + [f"buffsentinel__buffsentinel-0-vorstellung-{n}.md" for n in range(2, 11)] \
                + ["guildsentinel__guildsentinel-0-vorstellung.md", "buffsentinel__buffsentinel-0-vorstellung.md"]:
            self.assertNotIn(fn, todo)
            self.assertIn(fn, why)


if __name__ == "__main__":
    unittest.main()
