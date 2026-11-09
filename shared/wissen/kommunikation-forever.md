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

## Quellen
- https://github.com/Offroads/WoWForeverRace/pull/48
- https://github.com/Shtian/bff-wow/pull/133
- https://x.com/TromaFR/status/2118734489618624939
- https://us.forums.blizzard.com/en/wow/t/wow-forever-custom-chat-channels-not-working-crossrealm-not-game-mode/2370263
