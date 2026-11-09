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
| **Ein Realm mit Layern** (z. B. "Europa PvP"). Kanal-Mitgliederliste zeigte beide Spieler; während des ersten Laufs wechselte der Layer (AutoLayer "1 -> 2") – alles kam trotzdem an. | T4 gleicher Kanal; Layerwechsel im Chat | belegt: Flüstern über einen Layerwechsel hinweg; vermutet: Flüstern zwischen verschiedenen Layern (Partner-Layer nicht bekannt) |

Folgerungen für das Flüster-Netz von GoldSentinelSync:
- Namen immer vollständig speichern und so verwenden, wie `CHAT_MSG_ADDON` sie liefert (mit Leerzeichen); nie am ersten
  Leerzeichen abschneiden.
- Erreichbarkeit nicht an der Rückgabe messen, sondern an der Systemmeldung "kein Spieler … online" (Offline merken,
  Meldung ausblenden) und an Antworten.
- Die Drossel von GoldSentinelSync (5/s für alle Addons) liegt weit unter dem Gemessenen und bleibt.

## Quellen
- https://github.com/Offroads/WoWForeverRace/pull/48
- https://github.com/Shtian/bff-wow/pull/133
- https://x.com/TromaFR/status/2118734489618624939
- https://us.forums.blizzard.com/en/wow/t/wow-forever-custom-chat-channels-not-working-crossrealm-not-game-mode/2370263
