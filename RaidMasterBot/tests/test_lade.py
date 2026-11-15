"""D-3 Lade-Test (ab Bot 1.5.146, Regel der Prüf-Sitzung 15.11. 20:48): jedes Bot-Modul importieren und alle in ihm
benutzten Namen auflösen. Ein Name, der gelesen, aber im Modul nirgends gebunden wird (Zuweisung, Parameter, Import,
def/class, except … as, global) und kein eingebauter Name ist, ist ein FEHLER – genau der Fehler, der beim Verschieben
von Code aus bot.py in ein Modul entsteht (er zeigte sich sonst erst beim ersten Aufruf).
"""
import ast
import builtins
import importlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bot_quelle  # noqa: E402

BUILTIN = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__builtins__"}


def unbound(src: str) -> list[tuple[int, str]]:
    tree = ast.parse(src)
    bound = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, ast.arg):
            bound.add(n.arg)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                bound.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            bound.update(n.names)
        elif isinstance(n, ast.MatchAs) and n.name:
            bound.add(n.name)
    return sorted({(n.lineno, n.id) for n in ast.walk(tree)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in bound | BUILTIN})


class Lade(unittest.TestCase):
    def test_alle_namen_aufloesbar(self):
        for p in bot_quelle.dateien():
            with open(p, encoding="utf-8") as f:
                bad = unbound(f.read())
            self.assertEqual(bad, [], f"{os.path.basename(p)}: Namen ohne Definition/Import {bad}")

    def test_module_importierbar(self):
        sys.path.insert(0, bot_quelle.BOT_DIR)
        from bot_harness import load_bot                    # zuerst: lädt kern aus der Testkopie (mit Attrappen-config)
        load_bot()                                          # – sonst würde "import grund" kern aus dem Repo laden
        # bot.py und kern.py: unten über bot_harness (kern liest config.json neben sich); Sammler braucht requests
        skip = {"bot.py", "kern.py", "markt_bericht_holen.py"}
        for p in bot_quelle.dateien():
            name = os.path.basename(p)
            if name in skip:
                continue
            importlib.import_module(name[:-3])
        from bot_harness import load_bot                    # bot.py selbst über die Attrappen-config
        b, _ = load_bot()
        import bot_hilfen                                   # aus bot_hilfen übernommen (D-3 Schritt 1)
        self.assertIs(sys.modules["anmeldung_bot"].raid_view, bot_hilfen.raid_view)   # D-3 Schritt 33
        import kern
        self.assertIs(b.cfg, kern.cfg)                           # D-3 Schritt 2: dieselben Objekte, nur einmal
        self.assertIs(b.state, kern.state)
        self.assertIs(sys.modules["raid_bot"].kills_db, kern.kills_db)   # bot.py braucht kills_db ab 1.5.179 nicht mehr
        self.assertEqual(os.path.dirname(kern.__file__), os.path.dirname(b.__file__))
        import grund
        self.assertIs(grund.bot, b.bot)                          # D-3 Schritt 3: Grundfunktionen mit demselben Bot
        self.assertIs(b.channel_by_id, grund.channel_by_id)
        import markt_bot
        self.assertIs(markt_bot.bot, b.bot)                      # D-3 Schritt 4: Marktdaten-Modul
        self.assertIs(b.market_intake, markt_bot.market_intake)
        import rechte_bot
        self.assertIs(rechte_bot.bot, b.bot)                     # D-3 Schritt 5: Rechte-Modul
        self.assertIs(b.check_bot_rights, rechte_bot.check_bot_rights)
        self.assertIs(rechte_bot.post_bot_log, b.post_bot_log)
        import pn_bot
        self.assertIs(pn_bot.bot, b.bot)                         # D-3 Schritt 6: /pn-Modul
        self.assertIs(b.bot.tree.get_command("pn").callback, pn_bot.pn_cmd.callback)
        import symbole_bot
        self.assertIs(symbole_bot.bot, b.bot)                    # D-3 Schritt 7: Symbole/Emojis/Wowhead
        self.assertIs(b.state, symbole_bot.state)
        import ruhmeshalle_bot
        self.assertIs(ruhmeshalle_bot.bot, b.bot)                # D-3 Schritt 8: Ruhmeshalle
        self.assertIs(b.update_hall_of_fame, ruhmeshalle_bot.update_hall_of_fame)
        self.assertIs(ruhmeshalle_bot.class_emoji, symbole_bot.class_emoji)
        self.assertIs(ruhmeshalle_bot.kills_db, kern.kills_db)
        for name, fn in (("ruhmeshalle-aufraeumen", ruhmeshalle_bot.ruhmeshalle_aufraeumen_cmd),
                         ("erfolge", ruhmeshalle_bot.erfolge_cmd)):
            self.assertIs(b.bot.tree.get_command(name).callback, fn.callback)
        import uploader_bot
        self.assertIs(uploader_bot.bot, b.bot)                   # D-3 Schritt 9: Uploader-Versand
        self.assertIs(b.bot.tree.get_command("uploader").callback, uploader_bot.uploader_cmd.callback)
        self.assertEqual(uploader_bot.ADDON_DIR, os.path.join(os.path.dirname(b.__file__), "addon"))
        self.assertIs(uploader_bot.ADDON_DIR, kern.ADDON_DIR)
        import bank_bot
        self.assertIs(bank_bot.bot, b.bot)                       # D-3 Schritt 10: Gildenbank und Raidfähigkeit
        self.assertIs(b.post_guild_bank, bank_bot.post_guild_bank)
        self.assertIs(b.bot.tree.get_command("bank").callback, bank_bot.bank_cmd.callback)
        self.assertIs(bank_bot.item_emoji, symbole_bot.item_emoji)
        import regeln_bot
        self.assertIs(regeln_bot.bot, b.bot)                     # D-3 Schritt 11: Regeln
        self.assertIs(b.ensure_guild_rules, regeln_bot.ensure_guild_rules)
        self.assertIs(regeln_bot.post_guild_bank, bank_bot.post_guild_bank)
        import beute_bot
        self.assertIs(beute_bot.bot, b.bot)                      # D-3 Schritt 12: Beute-Datenbank
        self.assertIs(b.update_lootdb, beute_bot.update_lootdb)
        self.assertIs(beute_bot.ensure_dkp_rules, regeln_bot.ensure_dkp_rules)
        self.assertIs(sys.modules["raid_bot"].raid_channel, grund.raid_channel)
        self.assertIs(beute_bot.raid_channel, grund.raid_channel)
        import klassen_bot
        self.assertIs(klassen_bot.bot, b.bot)                    # D-3 Schritt 13: Klassenfarben
        self.assertIs(b.sync_class_roles, klassen_bot.sync_class_roles)
        self.assertIs(klassen_bot.book, b.book)
        import willkommen_bot
        self.assertIs(willkommen_bot.bot, b.bot)                 # D-3 Schritt 14: Willkommen
        self.assertIs(b.ensure_welcome, willkommen_bot.ensure_welcome)
        self.assertIs(willkommen_bot.is_chef, grund.is_chef)
        for name, fn in (("willkommen", willkommen_bot.welcome_cmd), ("einladung", willkommen_bot.welcome_invite_cmd)):
            self.assertIs(b.bot.tree.get_command(name).callback, fn.callback)
        import gildenname_bot
        self.assertIs(gildenname_bot.bot, b.bot)                 # D-3 Schritt 15: Gildenname
        self.assertIs(b.handle_name_post, gildenname_bot.handle_name_post)
        self.assertIs(gildenname_bot.ensure_welcome, willkommen_bot.ensure_welcome)
        self.assertIs(gildenname_bot.is_chef, grund.is_chef)
        self.assertIs(b.bot.tree.get_command("gildenname"), gildenname_bot.name_group)
        import befehlsliste_bot
        self.assertIs(befehlsliste_bot.bot, b.bot)               # D-3 Schritt 16: Befehlslisten
        self.assertIs(b.ensure_command_list, befehlsliste_bot.ensure_command_list)
        self.assertIs(befehlsliste_bot.name_poll, gildenname_bot.name_poll)
        import mitglieder_bot
        self.assertIs(mitglieder_bot.bot, b.bot)                 # D-3 Schritt 17: Mitglieder-Bereich
        self.assertIs(b.maintain_member_area, mitglieder_bot.maintain_member_area)
        self.assertIs(mitglieder_bot.ensure_welcome, willkommen_bot.ensure_welcome)
        import ankuendigung_bot
        self.assertIs(ankuendigung_bot.bot, b.bot)               # D-3 Schritt 18: Addon-Versionen, Ankündigungen
        self.assertIs(b.check_addon_release, ankuendigung_bot.check_addon_release)
        self.assertEqual(ankuendigung_bot.ADDON_DIR, kern.ADDON_DIR)
        import betrieb_bot
        self.assertIs(betrieb_bot.bot, b.bot)                    # D-3 Schritt 21: Server-Betrieb
        for name in ("backup_loop", "icon_map_loop", "tb_cleanup_loop"):
            self.assertIs(getattr(b, name), getattr(betrieb_bot, name), name)
        self.assertIs(b.bot.tree.get_command("daten-import").callback, betrieb_bot.import_cmd.callback)
        import pug_bot
        self.assertIs(pug_bot.bot, b.bot)                        # D-3 Schritt 22: PUG-Einladung
        self.assertIs(b.handle_member_join, pug_bot.handle_member_join)
        self.assertIs(b.bot.tree.get_command("pug-einladung").callback, pug_bot.pug_invite_cmd.callback)
        import ereignis_bot
        import handwerk_bot
        self.assertIs(ereignis_bot.bot, b.bot)                   # D-3 Schritt 23: Ereignisse, Berufe
        self.assertIs(handwerk_bot.bot, b.bot)
        self.assertIs(sys.modules["raid_bot"].create_raid_event, ereignis_bot.create_raid_event)
        self.assertIs(handwerk_bot.class_emoji, symbole_bot.class_emoji)
        import raidanzeige_bot
        import twink_bot
        self.assertIs(raidanzeige_bot.bot, b.bot)                # D-3 Schritt 24: Raid-Anzeige, Twinks
        self.assertIs(twink_bot.bot, b.bot)
        self.assertIs(b.update_raid_message, raidanzeige_bot.update_raid_message)
        self.assertIs(twink_bot.update_raid_message, raidanzeige_bot.update_raid_message)
        import ersatz_bot
        import skillung_bot
        self.assertIs(ersatz_bot.bot, b.bot)                     # D-3 Schritt 25: Ersatzbank, Skillung
        self.assertIs(skillung_bot.bot, b.bot)
        self.assertIs(sys.modules["anmeldung_bot"].offer_substitute, ersatz_bot.offer_substitute)
        self.assertIs(ersatz_bot.update_raid_message, raidanzeige_bot.update_raid_message)
        self.assertIs(skillung_bot.update_raid_message, raidanzeige_bot.update_raid_message)
        import beutepost_bot
        import dkp_nachricht_bot
        self.assertIs(beutepost_bot.bot, b.bot)                  # D-3 Schritt 27: Beute-Posts, DKP-Nachricht
        self.assertIs(dkp_nachricht_bot.bot, b.bot)
        self.assertIs(b.post_new_loot, beutepost_bot.post_new_loot)
        self.assertIs(b.send_raid_dms, dkp_nachricht_bot.send_raid_dms)
        for name in ("class_emoji", "item_emoji", "item_icon", "wowhead_tip"):   # Symbole nur aus symbole_bot
            self.assertIs(getattr(beutepost_bot, name), getattr(symbole_bot, name), name)
        import monatlich_bot
        self.assertIs(monatlich_bot.bot, b.bot)                  # D-3 Schritt 28: Monatliches, Raider des Monats
        self.assertIs(b.monthly_loop, monatlich_bot.monthly_loop)
        self.assertIs(monatlich_bot.hall_channel, ruhmeshalle_bot.hall_channel)
        self.assertIs(monatlich_bot.post_market_report, markt_bot.post_market_report)
        self.assertIs(monatlich_bot.post_raid_ready, bank_bot.post_raid_ready)
        import dkp_tafel_bot
        import testdaten_bot
        self.assertIs(dkp_tafel_bot.bot, b.bot)                  # D-3 Schritt 26: DKP-Tabellen, Testdaten
        self.assertIs(b.post_dkp_tables, dkp_tafel_bot.post_dkp_tables)
        self.assertIs(dkp_tafel_bot.send_test, testdaten_bot.send_test)
        import testupload_bot
        self.assertIs(testupload_bot.bot, b.bot)                 # D-3 Schritt 29: Testmodus
        self.assertIs(testupload_bot.send_test, testdaten_bot.send_test)
        self.assertIs(b.handle_test_upload, testupload_bot.handle_test_upload)
        self.assertIs(b.test_cleanup_loop, testupload_bot.test_cleanup_loop)
        import update_bot
        for mod in (pug_bot, betrieb_bot, update_bot):                # D-3 Schritt 19: Neustart nur in grund.py
            self.assertIs(mod.restart_soon, grund.restart_soon, mod.__name__)
        self.assertFalse(hasattr(b, "EXIT_CODE"))                       # nur grund.EXIT_CODE
        import update_bot
        self.assertIs(update_bot.bot, b.bot)                     # D-3 Schritt 20: Selbst-Update
        self.assertIs(b.update_loop, update_bot.update_loop)
        self.assertIs(update_bot.restart_soon, grund.restart_soon)
        self.assertIs(update_bot.check_addon_release, ankuendigung_bot.check_addon_release)
        import kanalpflege_bot
        self.assertIs(kanalpflege_bot.bot, b.bot)                # D-3 Schritt 30: Kanalpflege
        self.assertIs(b.sync_raid_visibility, kanalpflege_bot.sync_raid_visibility)
        self.assertIs(kanalpflege_bot.NO_PING, grund.NO_PING)
        self.assertIs(kanalpflege_bot.dkp_channel_for, dkp_tafel_bot.dkp_channel_for)
        import dkp_befehle_bot
        self.assertIs(dkp_befehle_bot.bot, b.bot)                # D-3 Schritt 31: DKP-Befehle
        self.assertIs(b.reload_dkp_if_needed, dkp_befehle_bot.reload_dkp_if_needed)
        import raid_bot
        self.assertIs(raid_bot.bot, b.bot)                       # D-3 Schritt 32: Raids
        self.assertIs(b.reminder_loop, raid_bot.reminder_loop)
        self.assertIs(raid_bot.reload_dkp_if_needed, dkp_befehle_bot.reload_dkp_if_needed)
        self.assertIs(raid_bot.update_raid_message, raidanzeige_bot.update_raid_message)
        import anmeldung_bot
        self.assertIs(anmeldung_bot.bot, b.bot)                  # D-3 Schritt 33: Anmeldung
        self.assertIs(b.bot.on_interaction, anmeldung_bot.on_interaction)

    def test_findet_fehlenden_namen(self):
        self.assertEqual(unbound("def f():\n    return cfg['x']\n"), [(2, "cfg")])
        self.assertEqual(unbound("import os\ndef f(a):\n    return os.path.join(a)\n"), [])


if __name__ == "__main__":
    unittest.main()
