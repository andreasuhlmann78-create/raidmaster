ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# GuildSentinel – Nacht-Analyse (Supervisor, 15.11.2026 abends)

Geprüfte Version: 0.9.39 (Repo GuildSentinel, 15.11.; download/GuildSentinel-0.9.39.zip; auf CurseForge).

## 1. Geschichte (Repo-Log 44 Commits, raidmaster/auftraege/GuildSentinel/, berichte/GuildSentinel/)
- bis 0.9.16: Gildenwerkzeug (Mitglieder, Twinks/Main, Chat-Filter, Ereignisse, Fortschritt).
- 0.9.17–0.9.22 (9.–10.11.): Gildenverwaltung (Admin.lua, geschützte Aktionen), Berufe-Abgleich, GoldSentinelSync 2 (kein eigener
  Kanal mehr – Addon-Nachrichten über eigene Kanäle kommen in Forever nicht an), Rezepte je Mitglied.
- 0.9.23–0.9.28 (10.–12.11.): Werbung nur über die Chat-Eingabe (ChatFrame_OpenChat, kein SendChatMessage an CHANNEL),
  Werbetext ≤ 251 Zeichen, UTF-8-sicher.
- 0.9.29–0.9.39 (13.–15.11.): Einladen über /ginvite in der Chat-Eingabe, Rechtsklick-Menü, Rekrutierung in Phasen, Altersfrage,
  Befehlsliste, Marktdaten-Netz (GoldSentinelMarkt v1 -> v2 -> v4), Werbetexte zur Auswahl.
- Offen laut offen-guildsentinel.txt: GA (Altersfrage im Client bestätigen), RP/RV im Client, GoldSentinelMarkt aktualisieren,
  CH-G später.

## 2. Was ich gemacht habe
- addon_check auf die Zip: OK, 1 Warnung "GoldSentinelMarkt.lua veraltete offizielle Fassung (Version 4) – Version 6".
- Testroutine im nachgebauten WoW (test/run_routine.lua) für 16001 (Forever), 11509 (Era), 20506 (TBC): je 16/16, 0 Fehler.
- Alle 27 Testskripte in test/ für Forever: 23 grün; rot: run_v6.lua 4, run_v7.lua 2, run_v8.lua 6 (siehe G-1).
- Code gelesen: Core.lua (ns.Chat, Kampfsperre), Comm.lua, Recruit.lua (Auto-Antworten, Begrüssung), Lead.lua (Offiziersnotizen),
  API.lua (geschützte Gildenfunktionen), Ticker in allen Dateien.
- Messdaten aus dem Spiel (GSSniperLog 15.11., Spiel-Profiler): GuildSentinel Spitze 58 ms, 3 Bilder über 50 ms in ~1 Std.

## 3. Befunde
### G-1 Alte Regressionstests rot und nicht nachgeführt (MITTEL) – GEMESSEN
run_v6.lua (Online-Hinweis mit Main ×4), run_v7.lua (Gruppensuche "Kanal betreten" ×2), run_v8.lua (Sprache, Offiziersnotiz,
Probezeit, Dungeon, Antwort, Kraut ×6). Stichprobe Lead.lua 76: Nicht-Offiziere werden weiter abgewiesen – nur der Meldetext ist
neu ("Offiziersnotizen können nur Offiziere schreiben."), der Test sucht den alten. "Kanal betreten" ist seit 0.9.20 absichtlich
weg. Das Verhalten scheint also richtig, aber diese Tests schlagen nicht mehr an, wenn dort wirklich etwas kaputtgeht.
Vorschlag (nach Freigabe): Tests nachführen oder als überholt markieren, und alle Skripte in einem Lauf mit Gesamtzahl prüfen.

### G-2 GoldSentinelMarkt v4 statt v6 (MITTEL)
GuildSentinel ist auf CurseForge, also bei Spielern ohne AHSentinel. Dort läuft v4: Feed in einem Stück und viel Speicher
(v5/v6 behoben). Mit AHSentinel gewinnt v6.

### G-3 Automatische Flüster-Antworten an Fremde ohne Gesamtgrenze (NIEDRIG–MITTEL, Risiko)
Recruit.lua ~850: Wer ein Schlüsselwort flüstert, bekommt nach 1,5 s automatisch eine Antwort (einmal je 10 Min. je Name) und
danach die Bewerbungsfragen. Es gibt eine Grenze je Name, aber keine Gesamtgrenze je Minute. Viele Fremde (oder Twinks) können
so viele automatische Flüsternachrichten auslösen. Das ist ein Missbrauchs- und Melde-Risiko (Blizzard-Regeln zu automatisierten
Nachrichten), zu prüfen. Begrüssung im Gildenchat: Abstimmung über "WEL"-Anspruch verhindert Doppelungen.

### G-4 Ruckeln gering (NIEDRIG) – GEMESSEN
Spitze 58 ms, 3 Bilder > 50 ms. Ursache nicht gemessen. Ticker: 1 s (nur bei sichtbarer Werbe-Seite), 30 s, 60 s, 300 s,
600 s, 1800 s – unauffällig.

### G-5 Altersfrage (Hinweis)
GA1 fragt Bewerber nach dem Alter (ab 16). Antworten werden lokal gespeichert. Datenschutz: nur speichern, was nötig ist
(Ja/Nein "mindestens 16" statt Zahl), und nichts davon in Sync/Uploader.

## 4. Was gut ist
- Geschützte Aktionen nur über die Chat-Eingabe bzw. einen sicheren Knopf, Kampfsperre, ns.Act/Testmodus loggt statt senden.
- Drei Spielversionen in der Testroutine, Sandbox, Recorder.
