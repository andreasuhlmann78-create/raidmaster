"""T-D-UPALT: PN an den Besitzer eines Rechners mit veraltetem Daten-Uploader (Auftrag Supervisor 24.11.2026 10:05) – ohne Netz.

Veraltet = "uploader" fehlt, "unbekannt" oder älter als VERSION in RaidMasterUploader/uploader.py; je Rechner zählt der Eintrag
mit der grössten "zeit" aus "sicherung" und main. Zuordnung nur über die Index-Nachricht in #sync-daten (Rechnername wie
daten.py path_name); mehrdeutig/unbekannt -> keine PN, nur eine Zahl in #bot-log (einmal). Höchstens 1 PN je Rechner und
neuester Version, nie an Gäste, nicht an Mitglieder, die die neueste Version schon per /uploader bekamen. Erster Lauf mit 2.3.20:
alle veralteten Rechner gelten als informiert (Offiziere 08:37). Zugangsschlüssel nirgends; #bot-log ohne Rechnernamen.
"""
import asyncio
import json
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

N = types.SimpleNamespace
GEHEIM = "ghp_TESTNURFUERTESTS0000000000000000"


class Mitglied:
    def __init__(self, uid, roles=("Offizier",), bot=False, closed=False):
        self.id, self.bot, self.closed = uid, bot, closed
        self.roles = [N(name=r) for r in roles]
        self.got = []

    async def send(self, text, **kw):
        if self.closed:
            import discord
            raise discord.Forbidden(N(status=403, reason="x"), "DMs zu")
        self.got.append(text)


class Gilde:
    def __init__(self, members):
        self.members = {m.id: m for m in members}

    def get_member(self, uid):
        return self.members.get(uid)


def index_text(*machines):
    idx = {"v": 2, "seq": 3, "machine": machines[0], "time": 1, "off": 0,
           "r": {f"wow_classic/KONTO{i}": [1, ["1"], m, 1] for i, m in enumerate(machines)}, "h": []}
    return "GSSYNC-INDEX – nicht ändern\n" + json.dumps(idx, separators=(",", ":"))


class Logik(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        load_bot()
        cls.m = sys.modules["uploader_alt_bot"]

    def test_veraltet(self):
        m = self.m
        st = {"A": {"zeit": 1}, "B": {"uploader": "unbekannt"}, "C": {"uploader": "2.3.19"},
              "D": {"uploader": "2.3.20"}, "E": {"uploader": "2.3.21"}, "F": {"uploader": "2.3.9"}}
        self.assertEqual(m.outdated(st, "2.3.20"), {"A": "", "B": "", "C": "2.3.19", "F": "2.3.9"})
        self.assertEqual(sorted(m.outdated(st, "2.3.21")), ["A", "B", "C", "D", "F"])

    def test_sicherung_und_main_neuester_eintrag(self):
        m = self.m
        sich = {"PC": {"zeit": 100, "uploader": "2.3.20"}, "LAP": {"zeit": 50, "uploader": "2.3.20"}}
        main = {"PC": {"zeit": 200}, "LAP": {"zeit": 40}, "NEU": {"zeit": 10, "uploader": "2.3.18"}}
        merged = m.merge_stands(sich, main, None, "kaputt")
        self.assertEqual(sorted(m.outdated(merged, "2.3.20")), ["NEU", "PC"])   # PC: main neuer und alt; LAP: sicherung neuer

    def test_index_rechnernamen(self):
        m = self.m
        self.assertEqual(m.machines_in_index(index_text("MEIN PC", "Laptop-2")), {"MEIN_PC", "Laptop-2"})
        self.assertEqual(m.machines_in_index('GSSYNC-INDEX\n{"seq":1,"machine":"Alt.PC.","parts":["1"]}'), {"Alt.PC"})
        self.assertEqual(m.machines_in_index("kein index"), set())
        self.assertEqual(m.machines_in_index("GSSYNC-INDEX {kaputt"), set())

    def test_mehrdeutig_ohne_besitzer(self):
        own, amb = self.m.owners({1: {"A", "B"}, 2: {"B", "C"}})
        self.assertEqual(own, {"A": 1, "C": 2})
        self.assertEqual(amb, {"B"})

    def test_gleiche_namensregel_wie_uploader(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "RaidMasterUploader"))
        try:
            import daten
        except ImportError:
            self.skipTest("RaidMasterUploader fehlt")
        for n in ("MEIN PC", "Ä-Rechner", ".x.", "", "PC_1.home"):
            self.assertEqual(self.m.path_name(n), daten.path_name(n), n)


class Ablauf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        load_bot()
        cls.m = sys.modules["uploader_alt_bot"]
        cls.dv = sys.modules["datenversand_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("_get_text", "read_stands", "read_indexes", "bot_guild", "post_bot_log")}
        self.saved_rc = self.dv.read_config
        self.saved_save = m.state.save
        self.saved_cfg = dict(m.cfg)
        self.saved_state = {k: m.state.data.get(k) for k in ("upalt_pn", "upalt_gemeldet", "uploader_geschickt")}
        for k in self.saved_state:
            m.state.data.pop(k, None)
        m.state.save = lambda: None
        m.cfg["update_repo"] = "owner/raidmaster"
        self.dv.read_config = lambda: (json.dumps({"repo": "owner/daten", "token": GEHEIM}).encode(), "")
        self.newest = "2.3.20"
        self.stand = {}
        self.index = {}
        self.blog, self.log = [], []

        self.minfile = "# Erklärung\n#\n2.3.20\n"

        async def get_text(session, url, what, headers=None):
            if "mindestversion" in url:
                return self.minfile
            return f'VERSION = "{self.newest}"\n'

        async def read_stands(session, repo, token):
            self.assertEqual((repo, token), ("owner/daten", GEHEIM))
            return [self.stand]

        async def read_indexes():
            return {uid: m.machines_in_index(index_text(*names)) for uid, names in self.index.items()}

        async def blog(text):
            self.blog.append(text)
        m._get_text, m.read_stands, m.read_indexes, m.post_bot_log = get_text, read_stands, read_indexes, blog
        self.off = Mitglied(11)
        self.off2 = Mitglied(12)
        self.chef = Mitglied(10, roles=("Gildenmeister",))
        self.gast = Mitglied(13, roles=("Gast",))
        self.zu = Mitglied(14, closed=True)
        self.gilde = Gilde([self.off, self.off2, self.chef, self.gast, self.zu])
        m.bot_guild = lambda: self.gilde

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        self.dv.read_config = self.saved_rc
        m.state.save = self.saved_save
        m.cfg.clear()
        m.cfg.update(self.saved_cfg)
        for k, v in self.saved_state.items():
            if v is None:
                m.state.data.pop(k, None)
            else:
                m.state.data[k] = v

    def run_once(self):
        return asyncio.run(self.m.check_once())

    def alle_texte(self):
        out = list(self.blog)
        for mem in self.gilde.members.values():
            out += mem.got
        return out

    def test_erster_lauf_2_3_20_niemand_angeschrieben(self):
        """Stand 10:00: PC des Chefs + 2 Offiziere ohne "uploader" -> keine PN (2.3.20 schon verteilt)."""
        self.stand = {"CHEF-PC": {"zeit": 1}, "OFF-A": {"zeit": 1}, "OFF-B": {"zeit": 1}, "GUT": {"zeit": 1, "uploader": "2.3.20"}}
        self.index = {10: ["CHEF-PC"], 11: ["OFF-A"], 12: ["OFF-B"]}
        r = self.run_once()
        self.assertEqual((r["old"], r["pn"]), (3, 0))
        self.assertEqual(self.off.got + self.off2.got + self.chef.got, [])
        self.assertEqual(self.m.state.data["upalt_pn"], {"CHEF-PC": "2.3.20", "OFF-A": "2.3.20", "OFF-B": "2.3.20"})
        self.assertEqual(len(self.blog), 1)
        self.run_once()                                  # zweiter Lauf: nichts Neues
        self.assertEqual(len(self.blog), 1)
        self.assertEqual(self.off.got, [])

    def test_neue_version_je_rechner_einmal(self):
        self.stand = {"OFF-A": {"zeit": 1}, "OFF-B": {"zeit": 1, "uploader": "2.3.20"}}
        self.index = {11: ["OFF-A"], 12: ["OFF-B"]}
        self.run_once()                                  # Seed mit 2.3.20 (OFF-A)
        self.newest = "2.3.21"
        r = self.run_once()
        self.assertEqual(r["pn"], 2)
        self.assertEqual(len(self.off.got), 1)
        self.assertEqual(len(self.off2.got), 1)
        self.assertIn("Dein Daten-Uploader ist veraltet – deine Daten werden nicht mehr angenommen. Bitte /uploader holen "
                      "(mindestens Version 2.3.21).", self.off.got[0])
        self.assertIn("`OFF-A`", self.off.got[0])
        self.run_once()
        self.run_once()
        self.assertEqual((len(self.off.got), len(self.off2.got)), (1, 1))   # höchstens 1 PN je Rechner und Version
        self.newest = "2.3.22"
        self.run_once()
        self.assertEqual((len(self.off.got), len(self.off2.got)), (2, 2))   # neue Version -> wieder genau 1

    def test_zwei_rechner_ein_mitglied_eine_pn(self):
        self.stand = {"PC": {"zeit": 1}, "LAPTOP": {"zeit": 1, "uploader": "2.3.19"}}
        self.index = {11: ["PC", "LAPTOP"]}
        self.m.state.data["upalt_pn"] = {}
        self.run_once()
        self.assertEqual(len(self.off.got), 1)
        self.assertIn("`LAPTOP`, `PC`", self.off.got[0])

    def test_gegenprobe_ohne_seed_wird_angeschrieben(self):
        """Gegenprobe zu Punkt 5: erster Lauf mit 2.3.21 -> die Offiziere bekommen die PN."""
        self.newest = "2.3.21"
        self.stand = {"OFF-A": {"zeit": 1, "uploader": "2.3.20"}}
        self.index = {11: ["OFF-A"]}
        self.run_once()
        self.assertEqual(len(self.off.got), 1)

    def test_nie_an_gaeste_bots_und_wer_es_per_uploader_bekam(self):
        self.m.state.data["upalt_pn"] = {}
        bot_m = Mitglied(15, bot=True)
        self.gilde.members[15] = bot_m
        self.stand = {"G": {"zeit": 1}, "B": {"zeit": 1}, "O": {"zeit": 1}, "WEG": {"zeit": 1}}
        self.index = {13: ["G"], 15: ["B"], 11: ["O"], 99: ["WEG"]}
        self.m.note_given(11, "2.3.20")
        self.m.note_given(11, "2.3.19")                  # nie zurück auf eine ältere
        self.assertEqual(self.m.state.data["uploader_geschickt"], {"11": "2.3.20"})
        r = self.run_once()
        self.assertEqual(r["pn"], 0)
        self.assertEqual(self.gast.got + bot_m.got + self.off.got, [])
        self.newest = "2.3.21"                           # Offizier hat 2.3.21 noch nicht per /uploader -> PN
        self.run_once()
        self.assertEqual(len(self.off.got), 1)
        self.assertEqual(self.gast.got, [])

    def test_ohne_besitzer_einmal_melden_pn_sobald_bekannt(self):
        self.m.state.data["upalt_pn"] = {}
        self.stand = {"FREMD": {"zeit": 1}, "DOPPELT": {"zeit": 1}}
        self.index = {11: ["DOPPELT"], 12: ["DOPPELT"]}
        r = self.run_once()
        self.assertEqual((r["pn"], r["unknown"]), (0, 2))
        self.assertIn("2 Rechner ohne eindeutigen Besitzer (1 bei mehreren Mitgliedern)", self.blog[-1])
        self.run_once()
        self.assertEqual(len(self.blog), 1)              # nur einmal melden
        self.index = {11: ["DOPPELT"], 12: ["FREMD"]}    # Besitzer jetzt eindeutig -> PN
        self.run_once()
        self.assertEqual((len(self.off.got), len(self.off2.got)), (1, 1))

    def test_pn_geschlossen_kein_neuer_versuch(self):
        self.m.state.data["upalt_pn"] = {}
        self.stand = {"Z": {"zeit": 1}}
        self.index = {14: ["Z"]}
        r = self.run_once()
        self.assertEqual((r["pn"], r["fail"]), (0, 1))
        self.assertIn("1 nicht zustellbar", self.blog[-1])
        self.run_once()
        self.assertEqual(len(self.blog), 1)

    def test_kein_geheimnis_keine_namen_im_log(self):
        self.m.state.data["upalt_pn"] = {}
        self.stand = {"GEHEIMER-PC": {"zeit": 1}, "X": {"zeit": 1}}
        self.index = {11: ["GEHEIMER-PC"]}
        self.run_once()
        for t in self.alle_texte():
            self.assertNotIn(GEHEIM, t)
            self.assertNotIn("owner/daten", t)
        for t in self.blog:
            self.assertNotIn("GEHEIMER-PC", t)
            self.assertNotIn("`X`", t)

    def test_mindestversion_d_upmin1(self):
        """2.3.23 neueste, Mindestversion 2.3.20: 2.3.20–2.3.22 liefern trotzdem nicht -> PN (mindestens 2.3.23); 2.3.23 ok.
        Neue kleine Version 2.3.24 ohne höhere Mindestversion: KEINE neue PN (D-UPD1 Punkt 1). Mindestversion 2.3.24: wieder je 1 PN."""
        self.m.state.data["upalt_pn"] = {}
        self.newest = "2.3.23"
        self.stand = {"A": {"zeit": 1, "uploader": "2.3.22"}, "B": {"zeit": 1, "uploader": "2.3.23"},
                      "C": {"zeit": 1, "uploader": "2.3.19"}}
        self.index = {11: ["A"], 12: ["B"], 10: ["C"]}
        r = self.run_once()
        self.assertEqual((r["newest"], r["latest"], r["pn"]), ("2.3.23", "2.3.23", 2))
        self.assertIn("(mindestens Version 2.3.23)", self.off.got[0])
        self.assertEqual((len(self.off.got), len(self.off2.got), len(self.chef.got)), (1, 0, 1))
        self.assertIn("nötig: mindestens 2.3.23", self.blog[-1])
        self.newest = "2.3.24"
        r = self.run_once()
        self.assertEqual((r["newest"], r["pn"]), ("2.3.23", 0))
        self.assertEqual((len(self.off.got), len(self.off2.got), len(self.chef.got)), (1, 0, 1))
        self.minfile = "# x\n2.3.24\n"
        r = self.run_once()
        self.assertEqual((r["newest"], r["pn"]), ("2.3.24", 3))
        self.assertEqual((len(self.off.got), len(self.off2.got), len(self.chef.got)), (2, 1, 2))

    def test_d_upd1_text_mit_j_nur_ab_2_3_24(self):
        m = self.m
        self.assertIn("mit j bestätigen", m.pn_text("2.3.25", ["2.3.24", "2.3.30"]))
        self.assertIn("installiert sie selbst", m.pn_text("2.3.31", ["2.3.29", "2.3.30"]))   # DC-UPD1: ab 2.3.29 ohne Frage
        self.assertIn("mit j bestätigen", m.pn_text("2.3.31", ["2.3.28", "2.3.30"]))      # ein Rechner fragt noch
        self.assertNotIn("mit j", m.pn_text("2.3.25", ["2.3.24", "2.3.23"]))     # ein Rechner ohne Rückfrage -> /uploader
        self.assertNotIn("mit j", m.pn_text("2.3.25", [""]))
        self.m.state.data["upalt_pn"] = {}
        self.newest, self.minfile = "2.3.25", "2.3.25\n"
        self.stand = {"A": {"zeit": 1, "uploader": "2.3.24"}, "B": {"zeit": 1, "uploader": "2.3.22"}}
        self.index = {11: ["A"], 12: ["B"]}
        self.run_once()
        self.assertIn("Neue Pflicht-Version des Uploaders (mindestens Version 2.3.25) – bitte im Uploader-Fenster mit j bestätigen "
                      "(oder /uploader holen).", self.off.got[0])
        self.assertIn("Bitte /uploader holen (mindestens Version 2.3.25)", self.off2.got[0])

    def test_d_upd1_update_ergebnis(self):
        import time
        now = int(time.time())
        self.m.state.data["upalt_pn"] = {}
        self.newest, self.minfile = "2.3.24", "2.3.20\n"
        self.stand = {
            "A": {"zeit": 1, "uploader": "2.3.24", "update": {"von": "2.3.24", "nach": "2.3.25",
                                                              "ergebnis": "fehlgeschlagen: Prüfsumme falsch", "zeit": now - 60}},
            "B": {"zeit": 1, "uploader": "2.3.25", "update": {"von": "2.3.24", "nach": "2.3.25", "ergebnis": "ok", "zeit": now}},
            "C": {"zeit": 1, "uploader": "2.3.24", "update": {"von": "2.3.23", "nach": "2.3.24",
                                                              "ergebnis": "fehlgeschlagen: alt", "zeit": now - 7 * 3600}},
            "G": {"zeit": 1, "uploader": "2.3.24", "update": {"von": "2.3.24", "nach": "2.3.25",
                                                              "ergebnis": "fehlgeschlagen: x", "zeit": now}}}
        self.index = {11: ["A"], 12: ["B"], 10: ["C"], 13: ["G"]}
        r = self.run_once()
        self.assertEqual((r["old"], r["upd_ok"], r["upd_fail"]), (0, 1, 2))
        self.assertEqual(len(self.off.got), 1)
        self.assertIn("❌ Uploader-Update fehlgeschlagen (Prüfsumme falsch) – die alte Version 2.3.24 läuft weiter. "
                      "Bitte /uploader holen.", self.off.got[0])
        self.assertEqual(self.off2.got + self.chef.got + self.gast.got, [])   # ok: keine PN; zu alt: keine; Gast: nie
        self.assertIn("1 erfolgreich, 2 fehlgeschlagen (1 PN geschickt)", self.blog[-1])
        self.assertNotIn("Prüfsumme", self.blog[-1])
        n = len(self.blog)
        self.run_once()
        self.assertEqual((len(self.off.got), len(self.blog)), (1, n))          # je Rechner und Zeit nur einmal
        self.stand["A"]["update"] = dict(self.stand["A"]["update"], zeit=now)  # neuer Versuch -> neue Meldung
        self.run_once()
        self.assertEqual(len(self.off.got), 2)

    def test_mindestversion_nicht_lesbar_nichts_tun(self):
        self.m.state.data["upalt_pn"] = {}
        self.newest = "2.3.23"
        self.minfile = None
        self.stand = {"A": {"zeit": 1, "uploader": "2.3.19"}}
        self.index = {11: ["A"]}
        self.assertIsNone(self.run_once())
        self.assertEqual(self.off.got, [])

    def test_required_und_echte_datei(self):
        m = self.m
        self.assertEqual(m.required("2.3.21", None), "2.3.21")
        self.assertEqual(m.required("2.3.23", "2.3.20"), "2.3.23")
        self.assertEqual(m.required("2.3.30", "2.3.20"), "2.3.23")
        self.assertEqual(m.required("2.3.30", "2.3.25"), "2.3.25")
        self.assertIsNone(m.required("2.3.23", None))
        path = os.path.join(os.path.dirname(__file__), "..", "..", "RaidMasterUploader", "mindestversion.txt")
        with open(path, encoding="utf-8") as f:
            self.assertEqual(m.parse_minimum(f.read()), "2.3.20")
        self.assertIsNone(m.parse_minimum("# nur Kommentar\n"))

    def test_fehlt_etwas_nichts_tun(self):
        self.stand = {"A": {"zeit": 1}}
        self.index = {11: ["A"]}
        self.dv.read_config = lambda: (None, "fehlt")
        self.assertIsNone(self.run_once())
        self.dv.read_config = lambda: (json.dumps({"repo": "owner/daten", "token": GEHEIM}).encode(), "")
        self.newest = "kaputt"
        self.assertIsNone(self.run_once())
        self.assertNotIn("upalt_pn", self.m.state.data)   # kein Seed, solange die neueste Version unbekannt ist
        self.assertEqual(self.off.got, [])


if __name__ == "__main__":
    unittest.main()
