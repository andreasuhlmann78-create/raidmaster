# Addon-Kommunikation in WoW Forever – was geht, was nicht

Stand 9. November 2026. Gepflegt von der Prüf-Sitzung. Gilt für alle GoldSentinel-Addons mit Sync.

## Belegt
| Befund | Belege |
|---|---|
| **Addon-Nachrichten in eigenen Chat-Kanälen kommen NICHT an.** `C_ChatInfo.SendAddonMessage(prefix, msg, "CHANNEL", n)` gibt 0 zurück (Client nimmt an), der Server antwortet mit `CHAT_MSG_CHANNEL_NOTICE` `NOT_ALLOWED_IN_CHANNEL`; zugestellt wird nichts. Beitreten und Mitgliederliste funktionieren. | WoWForeverRace PR #48 (gemessen 5.11.2026, jeder getestete Spieler-Kanal); bff-wow PR #133 (5.11.2026, "never delivered"); Overlord-Autor auf X ("WoW Forever now refuses addon messages … on custom Channels"); bei uns: AHSentinel "0 Mitspieler", obwohl 2 Gildenmitglieder AHSentinel haben |
| **Eigene Kanäle sind nach internen Realms getrennt:** Ein Spielmodus hat mindestens zwei interne Realms; derselbe Kanalname ergibt auf dem anderen internen Realm einen getrennten Kanal. | Blizzard-Forum, Bug-Report 2.10.2026 (Beta), keine Blizzard-Antwort |
| **Gilden-Addon-Nachrichten funktionieren.** | GuildSentinel-Protokolle 9.11.: "BERUFE empfangen: 2 Einträge, angenommen 2" |
| **Addon-Flüstern (WHISPER) funktioniert** und ist der Ersatzweg anderer Addons. | bff-wow PR #133, WoWForeverRace PR #48 |
| **Höchstens 10 Kanäle je Spieler.** Bei uns 9/10 belegt (4 davon von unseren Addons: AHAPSync, GuildSentinelLFG, LevelPilotNet, BuffSentinelSync). | Screenshot 9.11. 18:03 |
| In Instanzen keine Addon-Nachrichten senden (laut WoWForeverRace). | WoWForeverRace PR #48 – bei uns noch nicht gemessen |

## Folgerungen
1. **Nie Daten über einen eigenen Kanal senden.** Ein Kanal dient höchstens dazu, Mitspieler zu FINDEN (Mitgliederliste).
2. **Wege in dieser Reihenfolge:** GUILD (Gilde), PARTY/RAID (Gruppe), WHISPER an bekannte Mitspieler (gedrosselt).
3. `NOT_ALLOWED_IN_CHANNEL` auswerten und den Kanal für die Sitzung als "verweigert" markieren.
4. Senden mit 0 als Rückgabe heisst nur "angenommen", nicht "angekommen" – Ankunft nur durch Antwort (Ping/Pong) belegbar.
5. Ein gemeinsamer Kanal für alle GoldSentinel-Addons statt vier (Kanalplätze).
6. **Alle Spielversionen müssen gehen** (Era, TBC/Anniversary, Mists, Retail, Forever): GUILD, PARTY/RAID und WHISPER
   gibt es überall – sie sind der Standardweg. Nicht nach Version verzweigen, sondern Fähigkeiten zur Laufzeit erkennen
   (Kanal verweigert? C_ChatInfo vorhanden? geschützte Werte?). Ob Kanal-Addon-Nachrichten in Retail oder Era
   ankommen, ist hier NICHT belegt – darum nie darauf verlassen.

## Gemessen mit GSMesstest (9. November 2026, 19:05 und 19:11, zwei Spieler, Client 1.60.1)
Werkzeug: `shared/messtest/GSMesstest`, Rohdaten vom Nutzer (SavedVariables), zwei vollständige Läufe nacheinander.

| Befund | Messung | Stufe |
|---|---|---|
| **Addon-Flüstern kommt an, in beide Richtungen.** | 10/10 hin, 10/10 zurück, 200 Zeichen je Nachricht, zweimal | belegt |
| **Keine Drossel bis mindestens 20/s und 30 Nachrichten im selben Frame** (je 200 Zeichen): nichts verloren. | 20 mit 10/s, 50 mit 20/s, 30 auf einmal – je zweimal vollständig (Zähler 40/20, 100/50, 60/30 = zwei Läufe) | belegt |
| **Rückgabe von SendAddonMessage ist immer 0** – auch an Offline- und unbekannte Spieler. Sagt nichts über die Ankunft. | alle Sendungen "ret 0" | belegt |
| **Flüstern an Offline- oder unbekannte Spieler** erzeugt beim Sender `CHAT_MSG_SYSTEM` "Momentan ist kein Spieler mit dem Namen '<Name>' online." (ERR_CHAT_PLAYER_NOT_FOUND_S). **Ein Chat-Filter kann sie ausblenden.** | beide Fälle, Filter griff | belegt |
| **Charakternamen in Forever haben Vor- und Nachnamen mit Leerzeichen.** Flüstern nur mit dem Vornamen kommt nicht an; der ganze Name ("Vorname Nachname") funktioniert auch als Ziel von Addon-Flüstern. | Nutzer: Vorname allein nicht angekommen; Messung mit ganzem Namen | belegt |
| **Ein Realm mit Layern** (z. B. "Europa PvP"). Kanal-Mitgliederliste zeigte beide Spieler (gleicher Kanal). Die Meldung "Layer changed 1 -> 2" des Addons AutoLayer während der Messung war laut Nutzer eine **Falschmeldung** – kein Layerwechsel belegt. | T4 gleicher Kanal | belegt: gleicher Kanal; **offen (Messauftrag):** Flüstern zwischen verschiedenen Layern – mit einem Partner wiederholen, der sicher auf einem anderen Layer ist |

Folgerungen für das Flüster-Netz von GoldSentinelSync:
- Namen immer vollständig speichern und so verwenden, wie `CHAT_MSG_ADDON` sie liefert (mit Leerzeichen); nie am ersten
  Leerzeichen abschneiden.
- Erreichbarkeit nicht an der Rückgabe messen, sondern an der Systemmeldung "kein Spieler … online" (Offline merken,
  Meldung ausblenden) und an Antworten.
- Die Drossel von GoldSentinelSync (5/s für alle Addons) liegt weit unter dem Gemessenen und bleibt.

## GoldSentinelSync 2 – Flüster-Netz (gebaut 9. November 2026)
- Jeder Client merkt sich Mitspieler mit Sync 2 (aus Gilde, Gruppe, Flüstern, Listen anderer Clients), nur lokal, nur
  Namen und Zeiten (`ep:UseStorage(DB)` -> `DB.gsSync`).
- `ep:Send(text)`: Gilde + Gruppe wie bisher, dazu Flüstern an 3 Netz-Mitspieler ausserhalb der eigenen Gilde
  (Kopf `#S2:<sid>:<n>:<Weitergabe>:`). Wer sie bekommt, bringt sie in seine Gilde/Gruppe (`#S1`, gleiche Kennung) und
  gibt sie an 3 weitere (höchstens 2-mal). Dubletten über die Kennung.
- Alle 10 Minuten eine Liste mit bis zu 8 Namen an 2 Mitspieler; neue Namen werden per Flüstern vorgestellt (höchstens
  2 alle 30 s), danach kennen sich beide direkt. So wächst das Netz über alle Gilden.
- Gedrosselt: 40 Netz-Flüsternachrichten pro Minute, nur wenn Gilde/Gruppe nichts zu senden haben, nicht im Kampf.
- Offline: "kein Spieler … online" nach eigenem Flüstern -> Spieler 15 Minuten Pause, Meldung ausgeblendet; nach 5 Fehlschlägen
  oder 30 Tagen ohne Lebenszeichen vergessen.
- Clients mit Sync 1 bekommen nie `#S2` (nur Mitspieler, die "~sync=2" gemeldet haben).
- Grenze: Das Netz erreicht nur, wer irgendwann über Gilde, Gruppe oder eine Liste mit dem Netz in Kontakt kam.

## Messauftrag M5 – Addon-Nachrichten über YELL/SAY (offen, Werkzeug: GSMesstest 4, `/gsmess rufen`)
- Frage: Tragen YELL/SAY Addon-Nachrichten an Spieler in der Nähe, auch ohne Gilde/Gruppe? Bei Blizzard (Retail ab
  8.x) sind SAY/YELL für Addon-Nachrichten ausserhalb von Instanzen gesperrt (vermutet, nicht für Forever gemessen).
- Wenn ja: Entdeckung neuer Netz-Mitspieler am Auktionshaus/in Städten möglich (nur Kennung "habe Sync 2" rufen, Rest
  per Flüstern). Wenn nein: Entdeckung bleibt bei Gilde, Gruppe, Listen und normalen Kontakten.
- **Ergebnis 10.11. 18:19 (GSMesstest 4, Undercity am AH, Client 1.60.1): BELEGT – geht NICHT.**
  SendAddonMessage mit "YELL" und mit "SAY" gibt **4 zurück = Enum.SendAddonMessageResult.InvalidChatType**: der
  Client lehnt den Weg schon beim Senden ab (wie bei Blizzard ausserhalb von Instanzen). Kein eigenes Echo, keine
  Antwort, und seit dem Einloggen keine einzige fremde Addon-Nachricht über SAY/YELL.
- Folge: Entdeckung über Rufweite ist in Forever nicht möglich. Neue Netz-Mitspieler nur über Gilde, Gruppe/Raid,
  Flüstern und die Listen anderer Clients (Sync 2). Ideen dafür: gemeinsames GoldSentinel-Adressbuch aller Addons,
  Kontakte aus normalem Spiel (Handel, Flüstern, Post, Einladung) als Kandidaten per Addon-Flüstern anfragen.
  Entscheid des Nutzers 10.11. 18:22: Es bleibt so – kein Adressbuch, keine Kontakt-Anfragen beauftragen.
  Nicht prüfen: Instanzen (dort könnte SAY/YELL erlaubt sein) – für ein AH-Netz ohne Nutzen.

## Quellen
- https://github.com/Offroads/WoWForeverRace/pull/48
- https://github.com/Shtian/bff-wow/pull/133
- https://x.com/TromaFR/status/2118734489618624939
- https://us.forums.blizzard.com/en/wow/t/wow-forever-custom-chat-channels-not-working-crossrealm-not-game-mode/2370263
