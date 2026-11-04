"""Offline-Test (Bot 1.5.106): Befehlslisten #befehlsliste (Offiziere) und #befehle (Mitglieder).
Liest bot.py als Text (ohne den Bot zu starten):
- jeder Slash-Befehl steht in COMMAND_INFO (sonst fehlt er in #befehle oder steht unter "Sonstiges")
- kein Befehl mit Rechteprüfung (is_creator/is_admin) gilt als "alle" -> nie in der Liste für Mitglieder
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import ast
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import server_setup  # noqa: E402

with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as _f:
    SRC = _f.read()


def command_info() -> dict:
    m = re.search(r"^COMMAND_INFO = (\{.*?^\})", SRC, re.S | re.M)
    body = re.sub(r"#[^\n]*", "", m.group(1))
    return ast.literal_eval(body)


def commands() -> dict:
    """{'raid erstellen': Rumpf der Funktion, …} – alle Slash-Befehle aus bot.py."""
    groups = dict(re.findall(r'^(\w+)\s*=\s*app_commands\.Group\(name="([^"]+)"', SRC, re.M))
    out = {}
    for m in re.finditer(r'^@(bot\.tree|\w+)\.command\(name="([^"]+)"', SRC, re.M):
        start = SRC.index("\nasync def ", m.end())
        nxt = re.search(r"^(?:async def |def |@|class |[A-Z_]+ = )", SRC[start + 12:], re.M)
        body = SRC[start: start + 12 + (nxt.start() if nxt else len(SRC))]
        grp = m.group(1)
        out[m.group(2) if grp == "bot.tree" else f"{groups.get(grp, grp)} {m.group(2)}"] = body
    return out


class Befehle(unittest.TestCase):
    def test_alle_befehle_eingetragen(self):
        info, cmds = command_info(), commands()
        self.assertGreater(len(cmds), 35)
        self.assertEqual(sorted(set(cmds) - set(info)), [], "Befehle fehlen in COMMAND_INFO")

    def test_kein_offiziersbefehl_fuer_alle(self):
        info, cmds = command_info(), commands()
        for name, body in cmds.items():
            first = body.split("\n")[:6]                     # Rechteprüfung steht am Anfang der Funktion
            guarded = any(re.search(r"if not (is_creator|is_admin)\(", ln) for ln in first)
            if guarded:
                self.assertNotEqual(info.get(name, ("?",))[0], "alle", f"/{name} prüft Rechte, steht aber für alle")

    def test_stichproben(self):
        info = command_info()
        for n in ("dkp", "charakter", "twink hinzufügen", "bank", "beute boss", "handwerk"):
            self.assertEqual(info[n][0], "alle", n)
        for n in ("raid erstellen", "raid testraid", "beute entfernen", "update", "uploader", "raid-ereignisse"):
            self.assertEqual(info[n][0], "Gildenleitung", n)


class Kanal(unittest.TestCase):
    def test_befehle_in_allgemein_nur_bot_schreibt(self):
        general = next(c for c in server_setup.BASE_BOTTOM if c["name"] == server_setup.GENERAL)
        spec = next(c for c in general["channels"] if c[1] == "befehle")
        self.assertEqual((spec[0], spec[3]), ("text", "botonly"))
        self.assertFalse(general.get("guest"))                # Gäste (PUG) sehen 💬 ALLGEMEIN nicht

    def test_befehlsliste_bei_offizieren(self):
        off = next(c for c in server_setup.BASE_TOP + server_setup.BASE_BOTTOM if c["name"] == "🔒 OFFIZIERE")
        self.assertIn("befehlsliste", [c[1] for c in off["channels"]])

    def test_vorhandener_kanal_unter_alias(self):
        from types import SimpleNamespace as N
        self.assertEqual(server_setup.find_channel([N(name="commands")], "befehle").name, "commands")


class Role:
    def __init__(self, name):
        self.name = name


class NurWennFehlt(unittest.TestCase):
    """ensure_channel_if_missing: vorhandene Kanäle (auch unter Alias, irgendwo) nie anfassen, sonst anlegen."""

    def guild(self, channels):
        import asyncio  # noqa: F401
        from types import SimpleNamespace as N

        class G:
            def __init__(self):
                self.text_channels, self.voice_channels, self.roles, self.created = list(channels), [], [], []
                self.categories = [N(name=server_setup.GENERAL, id=5)]
                self.default_role, self.me = Role("@everyone"), Role("bot")        # Rechte-Schlüssel: hashbar

            async def create_category(self, name, **kw):
                c = N(name=name, id=6)
                self.categories.append(c)
                return c

            async def create_text_channel(self, name, **kw):
                c = N(name=name, id=7, category_id=kw["category"].id)
                self.created.append((name, kw.get("overwrites") is not None))
                self.text_channels.append(c)
                return c
        return G()

    def test_vorhanden_bleibt_unberuehrt(self):
        import asyncio
        from types import SimpleNamespace as N
        existing = N(name="Commands", id=1, category_id=99)             # Alias, andere Kategorie, Grossbuchstabe
        g = self.guild([existing])
        ch, rep = asyncio.run(server_setup.ensure_channel_if_missing(g, server_setup.GENERAL, "befehle", "t"))
        self.assertIs(ch, existing)
        self.assertEqual((g.created, rep, existing.category_id), ([], [], 99))

    def test_fehlt_wird_angelegt_nur_bot_schreibt(self):
        import asyncio
        g = self.guild([])
        ch, rep = asyncio.run(server_setup.ensure_channel_if_missing(g, server_setup.GENERAL, "befehle", "t"))
        self.assertEqual(ch.name, "befehle")
        self.assertEqual(g.created, [("befehle", True)])              # mit Rechten (botonly)
        self.assertTrue(any("befehle" in r for r in rep))


if __name__ == "__main__":
    unittest.main()
