"""D-3 Vorbereitung (Bot 1.5.145): Liste aller Slash-Befehle mit Parametern bleibt gleich.

Vergleicht die Befehle des echten bot.py (über bot_harness) mit tests/data/befehle.txt. Beim Aufteilen von bot.py in
Module (D-3) darf sich daran nichts ändern. Ist eine Änderung gewollt (neuer Befehl), die Datei neu schreiben:
    python3 -I RaidMasterBot/tests/test_befehle_liste.py --schreiben
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LISTE = os.path.join(HERE, "data", "befehle.txt")


def befehle() -> list[str]:
    from bot_harness import load_bot
    b, _ = load_bot()

    def walk(cmds, pre=""):
        out = []
        for c in cmds:
            sub = getattr(c, "commands", None)
            if sub is not None and not hasattr(c, "callback"):
                out += walk(sub, pre + c.name + " ")
            else:
                out.append(f"/{pre}{c.name}({', '.join(p.name for p in getattr(c, 'parameters', []))})")
        return out
    return sorted(walk(b.bot.tree.get_commands()))


class BefehleListe(unittest.TestCase):
    def test_gleiche_befehle(self):
        with open(LISTE, encoding="utf-8") as f:
            want = [x for x in f.read().splitlines() if x]
        have = befehle()
        self.assertEqual(have, want, "Slash-Befehle geändert – gewollt? Dann mit --schreiben neu erzeugen.")
        self.assertGreaterEqual(len(have), 49)


if __name__ == "__main__":
    if "--schreiben" in sys.argv:
        with open(LISTE, "w", encoding="utf-8") as f:
            f.write("\n".join(befehle()) + "\n")
        print("geschrieben:", LISTE)
    else:
        unittest.main()
