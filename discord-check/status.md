# Discord-Prüfung

Geprüft: 2026-11-13T16:43:22Z (Commit 8dbcdd8), Server: Alpine Vanguard

**Ergebnis: ❌ es fehlt etwas**

Der Bot holt Änderungen etwa alle 30 Minuten. 'wartet' = Push ist jünger als 45 Minuten.

## Addon-Veröffentlichungen (download/)

| | Addon | Version | Kanal | Gepostet | seit Push |
|---|---|---|---|---|---|
| ✅ ok | AHSentinel | 0.65.112 | #ahsentinel | 2026-11-13 16:23 UTC | 35 Min. |
| ❌ fehlt | RaidMaster | 3.0.25 | #raid-addon | - | 55 Min. |

## Ankündigungen (announce/, neueste Fassung je Reihe)

| | Datei | Kanal | Abdeckung | seit Push |
|---|---|---|---|---|
| ✅ ok | ahsentinel__ahsentinel-0.65.112.md | #ahsentinel | 100 % | 35 Min. |
| ✅ ok | ahsentinel__ahsentinel-0-vorstellung-1.8.md | #ahsentinel | 100 % | 4 Tage |
| ✅ ok | ahsentinel__ahsentinel-hilfe-1.0.md | #ahsentinel | 100 % | 9 Tage |
| ✅ ok | barrow-taktik__uebersicht-1.1.md | #barrow-taktik | 100 % | 10 Tage |
| ✅ ok | buffsentinel__buffsentinel-0.9.18.md | #buffsentinel | 100 % | 51 Min. |
| ⚠️ veraltet | guildsentinel__guildsentinel-0.9.37.md | #guildsentinel | 20 % | 59 Min. |
| ✅ ok | hyjal-taktik__uebersicht-1.1.md | #hyjal-taktik | 100 % | 10 Tage |
| ⚠️ veraltet | levelpilot__levelpilot-3.12.28.md | #levelpilot | 30 % | 54 Min. |
| ✅ ok | levelpilot__levelpilot-uebersicht-3.12.28.md | #levelpilot | 100 % | 54 Min. |
| ✅ ok | lore__alpine-vanguard-vorstellung-1.0.md | #lore | 100 % | 12 Tage |
| ✅ ok | mc-feuerresi__feuerresi-1.1.md | #mc-feuerresi | 100 % | 10 Tage |
| ✅ ok | onyxia-feuerresi__feuerresi-1.0.md | #onyxia-feuerresi | 100 % | 16 Tage |
| ✅ ok | onyxia-taktik__onyxia-video-1.0.md | #onyxia-taktik | 100 % | 17 Tage |
| ⚠️ veraltet | professionsentinel__professionsentinel-0.9.44.md | #professionsentinel | 25 % | 57 Min. |
| ✅ ok | professionsentinel__professionsentinel-0-vorstellung-1.27.md | #professionsentinel | 100 % | 12 Std. |
| ⚠️ veraltet | threatsentinel__threatsentinel-2.5.11.md | #threatsentinel | 40 % | 59 Min. |
| ✅ ok | threatsentinel__threatsentinel-0-vorstellung-2.2.md | #threatsentinel | 100 % | 11 Tage |
| ✅ ok | buffsentinel__buffsentinel-0-vorstellung-12.md | #buffsentinel | 100 % | 9 Tage |
| ✅ ok | guildsentinel__guildsentinel-0-vorstellung-19.md | #guildsentinel | 100 % | 33 Std. |
| ✅ ok | levelpilot__levelpilot-uebersicht.md | #levelpilot | 100 % | 17 Tage |

**announce/guildsentinel__guildsentinel-0.9.37.md** – fehlt im Discord:
- `📦 **GuildSentinel 0.9.37** – Marktdaten-Netz`
- `• GuildSentinel liest jetzt **Auktionshaus-Vollscans anderer Addons still mit** – nur Preise, Mengen und Absatz, **keine Namen** – und teilt sie anonym mit der `
- `• Standard an, ausschalten unter Einstellungen > **„Marktdaten teilen (anonym, nur Preise)“**. Nie im Kampf, nie ein eigener Scan.`
- `• Die Alters-Sperre gilt jetzt auch für Gildenverwaltung > Einladen.`

**announce/levelpilot__levelpilot-3.12.28.md** – fehlt im Discord:
- `📢 **LevelPilot 3.12.28** – Marktdaten-Netz`
- `LevelPilot hilft jetzt mit, den Markt auf WoW Forever komplett zu messen – gemeinsam mit allen GoldSentinel-Addons.`
- `• Macht **irgendein** Addon im Auktionshaus einen Vollscan, liest LevelPilot ihn still mit: tiefster Stückpreis, Menge und Anzahl Auktionen je Gegenstand.`
- `• Die Preise werden **anonym** mit Gilde und Netz geteilt – **keine Namen**, keine Abfrage, LevelPilot startet selbst nie einen Scan.`
- `• Läuft pro Spiel nur einmal, egal wie viele GoldSentinel-Addons du hast.`

**announce/professionsentinel__professionsentinel-0.9.44.md** – fehlt im Discord:
- `📦 **ProfessionSentinel 0.9.44** – Marktdaten-Netz 📈`
- `• **Marktdaten teilen:** ProfessionSentinel liest die Auktionshaus-Scans mit, die du sowieso machst (z. B. mit AHSentinel), und merkt sich je Item Preis, Menge `
- `• Kein zusätzlicher Scan, keine Abfrage. Ausschalten jederzeit: Rechtsklick auf den Minimap-Button oder `/ps markt``

**announce/threatsentinel__threatsentinel-2.5.11.md** – fehlt im Discord:
- `📦 **ThreatSentinel 2.5.11** – Marktdaten-Netz`
- `• ThreatSentinel trägt jetzt den gemeinsamen, anonymen Marktdaten-Leser der GoldSentinel-Addons mit: Wenn ein Auktionshaus-Addon einen Vollscan macht, werden di`
- `• Abschaltbar in den Einstellungen: „Marktdaten teilen (anonym, nur Preise)“`

## Bot-Funktionen (tut der Bot, was er soll?)

| | Prüfung | Ergebnis |
|---|---|---|
| ✅ ok | Kanäle aus /raidmaster-einrichten | alle da |
| ✅ ok | Regeln #verhaltensregeln | 2/2 Beiträge da |
| ✅ ok | Regeln #loot-regeln | 2/2 Beiträge da |
| ✅ ok | Regeln #gildenbank | 1/1 Beiträge da |
| ✅ ok | Regeln #ränge-und-aufnahme | 1/1 Beiträge da |
| ✅ ok | Regeln #pug-regeln | 2/2 Beiträge da |
| ✅ ok | Gildenbank: #gildenbank-bestand aufgelöst | Kanal weg |
| ✅ ok | Gildenbank: Bestand unter den Regeln | Reihenfolge stimmt |
| ✅ ok | Raid Molten Core | alle Kanäle da |
| ✅ ok | Raid Onyxias Hort | alle Kanäle da |
| ✅ ok | Raid Barrow Deeps | alle Kanäle da |
| ✅ ok | Raid Hyjalgipfel | alle Kanäle da |
| ✅ ok | Raid Pechschwingenhort ausgeblendet (noch nicht angekündigt) | für Mitglieder unsichtbar |
| ✅ ok | Raid Zul'Gurub ausgeblendet (noch nicht angekündigt) | für Mitglieder unsichtbar |
| ✅ ok | Raid Ruinen von Ahn'Qiraj ausgeblendet (noch nicht angekündigt) | für Mitglieder unsichtbar |
| ✅ ok | Raid Tempel von Ahn'Qiraj ausgeblendet (noch nicht angekündigt) | für Mitglieder unsichtbar |
| ✅ ok | Raid Naxxramas ausgeblendet (noch nicht angekündigt) | für Mitglieder unsichtbar |

## Nur zur Info (ohne Versionsnummer)

- ✅ announce/threatsentinel__threatsentinel-0-vorstellung.md in #threatsentinel: ok
