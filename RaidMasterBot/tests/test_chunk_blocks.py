"""T-CHUNK (Bot 1.5.162): raidmaster_data.chunk_blocks – keine Discord-Nachricht über 2000 Zeichen.

Befund 15.11.2026 (beim Test zu D-3 Schritt 16 gemessen): #befehlsliste Teil 3 hatte seit 1.5.141 2022 Zeichen,
weil ein einzelner Block (Abschnitt "Verwaltung") länger als das Limit war und ungeteilt blieb -> Discord lehnt
die Nachricht ab. Jetzt wird ein zu langer Block an Zeilengrenzen geteilt; alles andere bleibt wie bisher.
"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import raidmaster_data as rmd  # noqa: E402


def old_chunk_blocks(blocks, limit=1900):
    """Fassung bis 1.5.161 (zum Vergleich: bei Blöcken <= limit muss die neue Fassung gleich sein)."""
    out, cur = [], ""
    for b in blocks:
        if cur and len(cur) + len(b) + 2 > limit:
            out.append(cur)
            cur = ""
        cur = (cur + "\n\n" + b) if cur else b
    if cur:
        out.append(cur[:2000])
    return out


def lines_of(parts):
    return [ln for p in parts for ln in p.split("\n") if ln]


class ChunkBlocks(unittest.TestCase):
    def test_kurze_bloecke_wie_bisher(self):
        rnd = random.Random(7)
        for _ in range(300):
            blocks = ["\n".join("x" * rnd.randint(1, 120) for _ in range(rnd.randint(1, 12)))
                      for _ in range(rnd.randint(1, 15))]
            blocks = [b for b in blocks if len(b) <= 1900]
            self.assertEqual(rmd.chunk_blocks(blocks), old_chunk_blocks(blocks))

    def test_zu_langer_block_wird_geteilt(self):
        head = "🛠️ **Verwaltung**"
        block = head + "\n" + "\n".join(f"**`/befehl{i}`** – " + "b" * 90 for i in range(25))   # > 2000
        self.assertGreater(len(block), 2000)
        parts = rmd.chunk_blocks(["kurz", block, "danach"])
        self.assertTrue(all(len(p) <= 1900 for p in parts), [len(p) for p in parts])
        self.assertEqual(lines_of(parts), lines_of(["kurz", block, "danach"]))      # nichts verloren, Reihenfolge
        self.assertTrue(any(p.startswith(head) or ("\n" + head) in p for p in parts))

    def test_eine_zeile_allein_zu_lang(self):
        parts = rmd.chunk_blocks(["a" * 4500])
        self.assertEqual([len(p) for p in parts], [1900, 1900, 700])
        self.assertEqual("".join(parts), "a" * 4500)

    def test_nie_ueber_2000(self):
        rnd = random.Random(11)
        for _ in range(200):
            blocks = ["\n".join("y" * rnd.randint(1, 400) for _ in range(rnd.randint(1, 30)))
                      for _ in range(rnd.randint(1, 6))]
            parts = rmd.chunk_blocks(blocks)
            self.assertTrue(all(len(p) <= 2000 for p in parts))
            self.assertEqual("".join(lines_of(parts)), "".join(lines_of(blocks)))


if __name__ == "__main__":
    unittest.main()
