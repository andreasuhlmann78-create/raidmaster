# Testberichte der GoldSentinel-Addons

Ausgewertet: 2026-11-18 09:12 UTC

Weg: Addon -> SavedVariables -> RaidMasterUploader -> Discord #testberichte -> hier. Neue Berichte kommen beim nächsten /reload oder Ausloggen und dem nächsten Lauf des Uploaders.

| Addon | letzter Testlauf | Version | Client | OK | FEHLER | übersprungen | im Client prüfen | Fehler im Spiel (7 Tage) |
|---|---|---|---|---|---|---|---|---|
| AHSentinel | 18.11.2026 08:31 UTC | 0.65.343 | forever 1.60.1 (Interface 16001) | 2 | 4 | 3 | 0 | 63 |
| BuffSentinel | 18.11.2026 08:43 UTC | 0.9.55 | forever 1.60.1 (Interface 16001) | 213 | 1 | 11 | 10 | 307 |
| GuildSentinel | 18.11.2026 07:32 UTC | 0.9.56 | forever 1.60.1 (Interface 16001) | 320 | 0 | 23 | 8 | 5 |
| LevelPilot | 18.11.2026 08:40 UTC | 3.12.93 | forever 1.60.1 (Interface 16001) | 11 | 0 | 0 | 0 | 15 |
| ProfessionSentinel | 18.11.2026 07:50 UTC | 0.9.68 | forever 1.60.1 (Interface 16001) | 1 | 1 | 8 | 0 | 8 |
| RaidMaster | 18.11.2026 08:44 UTC | 3.0.35 | forever 1.60.1 (Interface 16001) | 138 | 0 | 15 | 10 | 0 |
| ThreatSentinel | 18.11.2026 08:44 UTC | 2.5.21 | forever 1.60.1 (Interface 16001) | 301 | 0 | 11 | 14 | 0 |

## Diagnose-Protokolle (GSDIAG1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| AHSentinel | 165 | `testberichte/diagnose/AHSentinel/0.65.343-ff200e1c4d9b.txt` |
| BuffSentinel | 55 | `testberichte/diagnose/BuffSentinel/0.9.55-d3c260ecc11f.txt` |
| GSMesstest | 11 | `testberichte/diagnose/GSMesstest/5.1-e71680805b41.txt` |
| GSSniperLog | 20 | `testberichte/diagnose/GSSniperLog/1.7-f8198d5ac74a.txt` |
| GuildSentinel | 165 | `testberichte/diagnose/GuildSentinel/0.9.56-e9c08c401f87.txt` |
| LevelPilot | 60 | `testberichte/diagnose/LevelPilot/3.12.93-9331c37a2e5f.txt` |
| ProfessionSentinel | 145 | `testberichte/diagnose/ProfessionSentinel/0.9.68-f6b623bc89a4.txt` |
| ThreatSentinel | 140 | `testberichte/diagnose/ThreatSentinel/2.5.21-66c8d12f9365.txt` |

## Wegdaten (GSWEGE1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| LevelPilot | 203 | `testberichte/wege/LevelPilot/LevelPilot-wege-1794940044-fbacb0.json` |

## AHSentinel

**Testlauf 0.65.278 · forever 1.60.1 (Interface 16001) · 16.11.2026 18:38 UTC** – OK 4 · FEHLER 1 · übersprungen 0 · im Client prüfen 0 · Sandbox FEHLER: 3 Pfade, wiederhergestellt: deCount.day, deCount.counted, deCount.since
- [FEHLER] T750 U – UI-CLEAN1 Fenster/Reiter/Unterreiter/Ansichten/Fenster/Dialoge (Klassisch/Modern, 100 %/130 %): nichts überlappt, nicht… (ergebnis: 727 Befunde (AH offen · Klassisch+Modern · 100+130 % · deDE · geprüft 152 von 156 Ansichten) · je Art: ragt heraus 182 · abgeschnitten 462 · überlappt 44 · veraltet 39 · je Ansicht: Kaufen > Schnäppchen: 86 · Kaufen > Schnäppchen > Unter Händlerpreis: 86 · Markt > Markt > Lücken: 65… | erwartet: 0 Befunde · geprüft m von m)

**Testlauf 0.65.315 · forever 1.60.1 (Interface 16001) · 17.11.2026 12:09 UTC** – OK 2 · FEHLER 5 · übersprungen 2 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 734 OK, 16 FEHLER, 26 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 4 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (ergebnis:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): FEHLER – 22 OK, 3 FEHLER, 4 übersprungen, Sandbox OK)
- [FEHLER] ALLES-5 ALLES – Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND) (ergebnis:   5. Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND): FEHLER – 149 Runden in 10 Min. · längste Wächter-Rechenzeit je Bild 61 ms (≤ 50) · längstes ganzes Bild 161 ms (Auskunft) · Hürden: Letzte Runde: 275 Angebote – 0 ohne Preissturz/Flutung)
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 58 OK, 6 FEHLER, 4 übersprungen, Sandbox OK)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): nicht prüfbar – Scan ohne Messung nach 10 Min.)
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: nicht prüfbar – Fenster nicht offen)

**Testlauf 0.65.328 · forever 1.60.1 (Interface 16001) · 17.11.2026 18:11 UTC** – OK 2 · FEHLER 4 · übersprungen 3 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 930 OK, 6 FEHLER, 30 übersprungen, Sandbox FEHLER: 2 Pfade, wiederhergestellt: sniper.stats.bought, sniper.stats.missed)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 4 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (ergebnis:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): FEHLER – 27 OK, 2 FEHLER, 1 übersprungen, Sandbox OK)
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 59 OK, 5 FEHLER, 4 übersprungen, Sandbox FEHLER: 1 Pfade, wiederhergestellt: sniper.targets.i:7048.found)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus) (Server-Abstand noch 15 Min.))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Testlauf 0.65.343 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:31 UTC** – OK 2 · FEHLER 4 · übersprungen 3 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 943 OK, 5 FEHLER, 30 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 5 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-5 ALLES – Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND) (ergebnis:   5. Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND): FEHLER – 175 Runden in 10 Min. · längste Wächter-Rechenzeit je Bild 54 ms (≤ 50) · längstes ganzes Bild 105 ms (Auskunft) · Hürden: Letzte Runde: 277 Angebote – 0 neu (nicht gerade abgelehnt))
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 61 OK, 5 FEHLER, 3 übersprungen, Sandbox OK)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus) (Server-Abstand noch 15 Min.))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Fehler im Spiel (letzte 7 Tage)**
- 25× `ADDON_ACTION_BLOCKED`: UNKNOWN() – Version 0.65.182, 0.65.189, 0.65.194, 0.65.196, 0.65.203 · forever 1.60.1 (Interface 16001) · zuletzt 15.11.2026 18:13 UTC
- 20× `ADDON_ACTION_FORBIDDEN`: UNKNOWN() – Version 0.65.16, 0.65.80 · forever 1.60.1 (Interface 16001) · zuletzt 11.11.2026 16:25 UTC
- 10× `Lua`: Interface/AddOns/AHSentinel/Seller.lua:1433: attempt to index local 'msg' (a secret string value, while execution tainted by 'AHSentinel') – Version 0.65.77 · forever 1.60.1 (Interface 16001) · zuletzt 10.11.2026 14:28 UTC
- 1× `Job:craft-top`: Interface/AddOns/AHSentinel/Crafting.lua:515: attempt to index field '?' (a nil value) – Version 0.65.138 · forever 1.60.1 (Interface 16001) · zuletzt 14.11.2026 06:53 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/UI_Main.lua:1303: script ran too long – Version 0.65.260 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 07:18 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1400: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:43 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1402: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:44 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/Ledger.lua:1686: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:44 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/Disenchant.lua:327: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:45 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1801: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:43 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/UI_Main.lua:1298: script ran too long – Version 0.65.315 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 11:24 UTC

## BuffSentinel

**Testlauf 0.9.7 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:19 UTC** – OK 120 · FEHLER 1 · übersprungen 10 · im Client prüfen 11 · Sandbox OK
- [CLIENT] T14 B – Talente in Forever lesbar? (anleitung: /dump BuffSentinel.talentsReadable, BuffSentinel.mainSpec – siehe T74)
- [FEHLER] T29 B – Ereignisse (ergebnis: fehlt: LEARNED_SPELL_IN_TAB · nach Kampfbeginn sichtbar: 0)
- [SKIP] T33 B – Debuffs reinigen (Testdaten) (grund: Reinigen-Raster in Forever/Retail aus)
- [CLIENT] T46 B – Töne hören (anleitung: Optionen > Warntöne > Anhören je Zeile und 'Sounds testen' in der Anordnen-Leiste: alle 7 Töne hörbar)
- [CLIENT] T55 B – Zauber-IDs im laufenden Client (anleitung: in Forever bestätigen – nicht aufgelöst: keine)
- [CLIENT] T74 C – Welche alten Funktionen hat Forever wirklich? (anleitung: /dump GetNumTalentTabs, GetTalentInfo, UnitBuff, GetSpellInfo, C_SpellBook ~= nil, ChatFrame_RemoveChannel, ChatFrameUtil, JoinTemporaryChannel)
- [SKIP] T80 D – Auren auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T81 D – Zauber auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T82 D – Zauberbuch auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T83 D – Gegenstände auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T84 D – Kampflog-Auslöser (grund: kein UnitBuff – moderner Client)
- [SKIP] T85 D – Hauptbaum nur in Cata (grund: kein UnitBuff – moderner Client)
- [SKIP] T87 D – Alter Kampfweg unverändert (grund: kein UnitBuff – moderner Client)
- [SKIP] T86 D – Fraktion in Era (grund: nur Classic Era)
- [CLIENT] T99 F – Nicht-deutscher Client (anleitung: einmal mit enUS-Client: Optionen öffnen, alle Seiten, Testmodus – Klassennamen aus LOCALIZED_CLASS_NAMES_MALE, Zauber in Client-Sprache, kein Fehler)
- [SKIP] T103 G – Andere Addons des Nutzers (grund: BuffSentinel hat keine Schnittstelle zu anderen GoldSentinel-Addons)
- [CLIENT] T104 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: BuffSentinel mit RaidMaster, GuildSentinel, ThreatSentinel, ProfessionSentinel laden: /gsgame eine Zeile, /reload ohne Lua-Fehler, /bsen fehler 'keine Fehler')
- [CLIENT] T106 H – RefreshGroup im Raid 40 (anleitung: im Raid /bsen testroutine leistung – Mittel < 5 ms)
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')

**Testlauf 0.9.54 · forever 1.60.1 (Interface 16001) · 18.11.2026 07:11 UTC** – OK 200 · FEHLER 13 · übersprungen 11 · im Client prüfen 10 · Sandbox OK
- [FEHLER] T141 K – Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern (ergebnis: BuffSentinelOptions überdeckt Pfeil (LevelPilot) · geprüft 1 | erwartet: keine)
- [CLIENT] T14 B – Talente in Forever lesbar? (anleitung: talentsReadable=false mainSpec=0 – /dump BuffSentinel.talentsReadable, BuffSentinel.mainSpec – siehe T74)
- [SKIP] T33 B – Debuffs reinigen (Testdaten) (grund: Reinigen-Raster in Forever/Retail aus)
- [FEHLER] T34 B – Gegner entzaubern (ergebnis: Magie nil, stehlbar nil, Wut nil/0)
- [CLIENT] T46 B – Töne hören (anleitung: Optionen > Warntöne > Anhören je Zeile und 'Sounds testen' in der Anordnen-Leiste: alle 7 Töne hörbar)
- [FEHLER] T155 B – Flüster-Netz: Mitspieler gespeichert, Nachrichten nur für Gilde/Gruppe nicht geflüstert (ergebnis: nein · 0/1)
- [SKIP] T247 B – Händlerdaten im echten Spiel (grund: wartet auf Händler – passiert von selbst beim nächsten Händler-Besuch (Entwicklermodus, 7 Tage))
- [FEHLER] T62 C – Debuff-Arten geschützt
- [SKIP] T80 D – Auren auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T81 D – Zauber auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T82 D – Zauberbuch auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T83 D – Gegenstände auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T84 D – Kampflog-Auslöser (grund: kein UnitBuff – moderner Client)
- [SKIP] T85 D – Hauptbaum nur in Cata (grund: kein UnitBuff – moderner Client)
- [SKIP] T87 D – Alter Kampfweg unverändert (grund: kein UnitBuff – moderner Client)
- [SKIP] T86 D – Fraktion in Era (grund: nur Classic Era)
- [CLIENT] T99 F – Nicht-deutscher Client (anleitung: einmal mit enUS-Client: Optionen öffnen, alle Seiten, Testmodus – Klassennamen aus LOCALIZED_CLASS_NAMES_MALE, Zauber in Client-Sprache, kein Fehler)
- [FEHLER] T100 G – Gemeinsame Dateien (ergebnis: geladen: RaidMaster,ThreatSentinel,AHSentinel,BuffSentinel,GuildSentinel,ProfessionSentinel,LevelPilot)
- [SKIP] T103 G – Andere Addons des Nutzers (grund: BuffSentinel hat keine Schnittstelle zu anderen GoldSentinel-Addons)
- [CLIENT] T104 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: BuffSentinel mit RaidMaster, GuildSentinel, ThreatSentinel, ProfessionSentinel laden: /gsgame eine Zeile, /reload ohne Lua-Fehler, /bsen fehler 'keine Fehler')
- [CLIENT] T106 H – RefreshGroup im Raid 40 (anleitung: im Raid /bsen testroutine leistung – Mittel < 5 ms)
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T147 J – Diagnose-Protokoll im Spiel (anleitung: /bsen protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt BuffSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')
- [FEHLER] T200 L – TU1 Lagen: jede Klasse/Skillung × jede Lage × Procs, Buffs, Abklingzeiten (ergebnis: 13 Klassen, 3684 Fälle, 4 Abweichungen · ROGUE/0 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/1 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/2 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/3 poisonstock B1 Buff fehlt ausser Kampf: ist n…)
- [FEHLER] T251 S – TU7 Lagen auf forever (ergebnis: 13 Klassen, 3684 Fälle, 4 Abweichungen · ROGUE/0 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/1 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/2 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/3 poisonstock B1 Buff fehlt ausser Kampf: ist n…)
- [FEHLER] T252 S – TU7 Lagen auf era (ergebnis: 13 Klassen, 3220 Fälle, 4 Abweichungen · ROGUE/0 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/1 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/2 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/3 poisonstock B1 Buff fehlt ausser Kampf: ist n…)
- [FEHLER] T253 S – TU7 Lagen auf tbc (ergebnis: 13 Klassen, 3400 Fälle, 4 Abweichungen · ROGUE/0 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/1 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/2 poisonstock B1 Buff fehlt ausser Kampf: ist nein, soll ja | ROGUE/3 poisonstock B1 Buff fehlt ausser Kampf: ist n…)
- [FEHLER] T158 Q – Regression 0.9.14-1: „Namen teilen“ aus sendet nichts, auch nicht an Gilde/Gruppe (ergebnis: 0/0/0 | erwartet: 0/2/4)
- [FEHLER] T136 I – Keine echten Aktionen während des Tests (senden, Chat, Kanal betreten) (ergebnis: echte Aktionen: 3, Haken: 3 von 3)
- [FEHLER] T162 Q – Regressionen: jeder Befund hat einen Test, der gelaufen ist (ergebnis: Regressionen: 28 von 28 vorhanden · FEHLER: 0.9.6-1 echte Aktionen gezählt; UI Oberfläche im Client (5.11.); SYNC Kanal/gemeinsamer Sync/Sync 2/Test 2 (9.11.); 0.9.14-1 Namen teilen aus -> nichts senden; TU1-Rest Proc mit Restzeit, Gruppenbuff von anderen)
- [FEHLER] T250 H – Bilder der Testroutine selbst (ergebnis: längstes Bild 45.3 ms (T146), Median der drei längsten 23.3 ms · höchstens 40 ms: nein · höchstens 2× Median: ja)

**Testlauf 0.9.55 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:43 UTC** – OK 213 · FEHLER 1 · übersprungen 11 · im Client prüfen 10 · Sandbox OK
- [CLIENT] T14 B – Talente in Forever lesbar? (anleitung: talentsReadable=false mainSpec=0 – /dump BuffSentinel.talentsReadable, BuffSentinel.mainSpec – siehe T74)
- [SKIP] T33 B – Debuffs reinigen (Testdaten) (grund: Reinigen-Raster in Forever/Retail aus)
- [CLIENT] T46 B – Töne hören (anleitung: Optionen > Warntöne > Anhören je Zeile und 'Sounds testen' in der Anordnen-Leiste: alle 7 Töne hörbar)
- [SKIP] T247 B – Händlerdaten im echten Spiel (grund: wartet auf Händler – passiert von selbst beim nächsten Händler-Besuch (Entwicklermodus, 7 Tage))
- [SKIP] T80 D – Auren auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T81 D – Zauber auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T82 D – Zauberbuch auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T83 D – Gegenstände auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T84 D – Kampflog-Auslöser (grund: kein UnitBuff – moderner Client)
- [SKIP] T85 D – Hauptbaum nur in Cata (grund: kein UnitBuff – moderner Client)
- [SKIP] T87 D – Alter Kampfweg unverändert (grund: kein UnitBuff – moderner Client)
- [SKIP] T86 D – Fraktion in Era (grund: nur Classic Era)
- [CLIENT] T99 F – Nicht-deutscher Client (anleitung: einmal mit enUS-Client: Optionen öffnen, alle Seiten, Testmodus – Klassennamen aus LOCALIZED_CLASS_NAMES_MALE, Zauber in Client-Sprache, kein Fehler)
- [SKIP] T103 G – Andere Addons des Nutzers (grund: BuffSentinel hat keine Schnittstelle zu anderen GoldSentinel-Addons)
- [CLIENT] T104 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: BuffSentinel mit RaidMaster, GuildSentinel, ThreatSentinel, ProfessionSentinel laden: /gsgame eine Zeile, /reload ohne Lua-Fehler, /bsen fehler 'keine Fehler')
- [CLIENT] T106 H – RefreshGroup im Raid 40 (anleitung: im Raid /bsen testroutine leistung – Mittel < 5 ms)
- [FEHLER] T110 H – Speicher (ergebnis: Müll je Aufruf: Refresh 0.00 KB, RefreshGroup 0.16 KB, ScanPlayerAuras 8.33 KB (Grenzen 2/4/2 KB))
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T147 J – Diagnose-Protokoll im Spiel (anleitung: /bsen protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt BuffSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')

**Fehler im Spiel (letzte 7 Tage)**
- 293× `Gruppe`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 06.11.2026 18:25 UTC
- 9× `Event UNIT_AURA`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 07.11.2026 19:30 UTC
- 3× `Event PLAYER_REGEN_ENABLED`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 10.11.2026 14:10 UTC
- 2× `Scan`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 11.11.2026 15:09 UTC

## GuildSentinel

**Testlauf 0.9.52 · forever 1.60.1 (Interface 16001) · 17.11.2026 17:49 UTC** – OK 303 · FEHLER 4 · übersprungen 23 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Allgemein: 'Bank-Charakter' anhaken, Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
- [CLIENT] T199 B – Verwaltungsknopf an der Gildenseite (anleitung: J drücken: rechts neben dem Gildenfenster steht 'Verwaltung (GuildSentinel)' (ohne Rechte grau); /gs verwaltung öffnet das Fenster; Passwort festlegen und mit falschem/richtigem Passwort entsperren)
- [FEHLER] T285 B – T-BL4: Chatfeld wird nie beschrieben (nur HookScript lesen, SetFocus) (lua: GuildSentinelCmdHint:SetPoint(): Wrong object type for function)
- [CLIENT] T191 B – Gilden-Berufsliste im Spiel (anleitung: Mit Gilde einloggen, 5 Minuten warten, /gs protokoll: Zeile 'Gilden-Berufsliste: … Zeilen' zeigt, ob das Spiel die Berufe der Mitglieder liefert; Seite Berufe zeigt dann auch Mitglieder ohne GuildSentinel (nur Stufen))
- [CLIENT] T106 C – echte Kampfsperre (anleitung: Berufe-Seite offen, Kampf beginnen: kein ADDON_ACTION_BLOCKED für GuildSentinel, nach dem Kampf ist der Knopf wieder da)
- [SKIP] T108 D – alter Client (grund: nicht dieser Client)
- [SKIP] T109 D – alter Client (grund: nicht dieser Client)
- [SKIP] T110 D – alter Client (grund: nicht dieser Client)
- [SKIP] T111 D – alter Client (grund: nicht dieser Client)
- [SKIP] T112 D – alter Client (grund: nicht dieser Client)
- [SKIP] T114 D – alter Client (grund: nicht dieser Client)
- [SKIP] T113 D – Berufe klassisch (grund: nicht dieser Client)
- [SKIP] T115 E – Neuinstallation (grund: würde GuildSentinelDB neu anlegen; offline: jeder Lauf in test/ startet ohne GuildSentinelDB)
- [SKIP] T117 E – Migration (grund: offline in test/run_nilglobals.lua (Altlasten) und run_lang.lua (alte Spracheinstellung))
- [SKIP] T119 E – beschädigte Einstellungen (grund: offline in test/run_nilglobals.lua)
- [SKIP] T123 F – alle Schlüssel vorhanden (grund: Client-Sprache ist de (Schlüssel bzw. Locales.lua))
- [CLIENT] T136 G – Guild Roster Manager (anleitung: mit installiertem GRM: Leitung > GRM-Import zeigt Zahlen; ohne: kein Fehler)
- [SKIP] T137 G – ProfessionSentinel (grund: GuildSentinel nutzt keine Schnittstelle von ProfessionSentinel)
- [SKIP] T145 H – Speicher (grund: Messung im Bericht unten (collectgarbage vor/nach))
- [CLIENT] T189 I – Diagnose-Protokoll im Spiel (anleitung: /gs protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt GuildSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T156 J – P4a: Bewerber-Flüstern im Kampf (grund: wie T85)
- [SKIP] T157 J – P4b: Addon-Nachricht im Kampf (grund: wie T84)
- [SKIP] T158 J – P4c: Abklingzeit im Kampf (grund: wie T86)
- [SKIP] T160 J – P5b: KnowsSpell über C_SpellBook (grund: wie T98/T133)
- [SKIP] T162 J – P6b: ChatFrame_RemoveChannel (grund: wie T101)
- [SKIP] T164 J – Launch-Tag: Interface-Nummer (grund: wie T03)
- [CLIENT] T168 J – K2 im echten Kampf (anleitung: Mitspieler flüstert im Kampf 'gilde'; nach dem Kampf /gs testroutine whisperq und prüfen, ob Hinweis oder Bewerber erscheint)
- [SKIP] T171 J – K5: tools/luac5.1 -v (grund: Werkzeug im Repo (offline))
- [SKIP] T172 J – RM2: Werkzeug nicht in der ZIP (grund: offline (unzip -l))
- [SKIP] T173 J – N8: Offline-Test K2 (grund: offline (test/run_forever95.lua))
- [FEHLER] T182 K – Tooltips verdecken keine Knöpfe (ergebnis: 486 Tooltips, verdeckt: home: "Unterstützen" -> Button in ?; members>list: "Unterstützen" -> Button in ?; members>list: Button in ? -> Button in ?; members>list: Button in ? -> Button in ?; members>list: Button in ? -> Button in ?; members>list: Button in ? -> Button in ?; members>list: Button in … | erwartet: 0)
- [FEHLER] T185 K – Texte passen (ergebnis: Knöpfe abgeschnitten: group>search: Button in ?; group>free: Button in ?; group>free: Button in ?; group>free: Button in ?; group>free: Button in ?; board>offer: Button in ?; poll>vote: Button in ?; prof>dir: Button in ?; prof>dir: Button in ?; prof>dir: Button in ? · WARNUNG 2 Texte zu lang: prog… | erwartet: 0 abgeschnittene Knöpfe)
- [FEHLER] T82 B – nichts gesendet (ergebnis: echt 1 (C_ChatInfo.SendAddonMessage 1), Warteschlange +0 | erwartet: echt 0, Warteschlange +0)

**Testlauf 0.9.53 · forever 1.60.1 (Interface 16001) · 17.11.2026 18:27 UTC** – OK 316 · FEHLER 1 · übersprungen 23 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Allgemein: 'Bank-Charakter' anhaken, Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
- [CLIENT] T199 B – Verwaltungsknopf an der Gildenseite (anleitung: J drücken: rechts neben dem Gildenfenster steht 'Verwaltung (GuildSentinel)' (ohne Rechte grau); /gs verwaltung öffnet das Fenster; Passwort festlegen und mit falschem/richtigem Passwort entsperren)
- [CLIENT] T191 B – Gilden-Berufsliste im Spiel (anleitung: Mit Gilde einloggen, 5 Minuten warten, /gs protokoll: Zeile 'Gilden-Berufsliste: … Zeilen' zeigt, ob das Spiel die Berufe der Mitglieder liefert; Seite Berufe zeigt dann auch Mitglieder ohne GuildSentinel (nur Stufen))
- [CLIENT] T106 C – echte Kampfsperre (anleitung: Berufe-Seite offen, Kampf beginnen: kein ADDON_ACTION_BLOCKED für GuildSentinel, nach dem Kampf ist der Knopf wieder da)
- [SKIP] T108 D – alter Client (grund: nicht dieser Client)
- [SKIP] T109 D – alter Client (grund: nicht dieser Client)
- [SKIP] T110 D – alter Client (grund: nicht dieser Client)
- [SKIP] T111 D – alter Client (grund: nicht dieser Client)
- [SKIP] T112 D – alter Client (grund: nicht dieser Client)
- [SKIP] T114 D – alter Client (grund: nicht dieser Client)
- [SKIP] T113 D – Berufe klassisch (grund: nicht dieser Client)
- [SKIP] T115 E – Neuinstallation (grund: würde GuildSentinelDB neu anlegen; offline: jeder Lauf in test/ startet ohne GuildSentinelDB)
- [SKIP] T117 E – Migration (grund: offline in test/run_nilglobals.lua (Altlasten) und run_lang.lua (alte Spracheinstellung))
- [SKIP] T119 E – beschädigte Einstellungen (grund: offline in test/run_nilglobals.lua)
- [SKIP] T123 F – alle Schlüssel vorhanden (grund: Client-Sprache ist de (Schlüssel bzw. Locales.lua))
- [CLIENT] T136 G – Guild Roster Manager (anleitung: mit installiertem GRM: Leitung > GRM-Import zeigt Zahlen; ohne: kein Fehler)
- [SKIP] T137 G – ProfessionSentinel (grund: GuildSentinel nutzt keine Schnittstelle von ProfessionSentinel)
- [SKIP] T145 H – Speicher (grund: Messung im Bericht unten (collectgarbage vor/nach))
- [CLIENT] T189 I – Diagnose-Protokoll im Spiel (anleitung: /gs protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt GuildSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T156 J – P4a: Bewerber-Flüstern im Kampf (grund: wie T85)
- [SKIP] T157 J – P4b: Addon-Nachricht im Kampf (grund: wie T84)
- [SKIP] T158 J – P4c: Abklingzeit im Kampf (grund: wie T86)
- [SKIP] T160 J – P5b: KnowsSpell über C_SpellBook (grund: wie T98/T133)
- [SKIP] T162 J – P6b: ChatFrame_RemoveChannel (grund: wie T101)
- [SKIP] T164 J – Launch-Tag: Interface-Nummer (grund: wie T03)
- [CLIENT] T168 J – K2 im echten Kampf (anleitung: Mitspieler flüstert im Kampf 'gilde'; nach dem Kampf /gs testroutine whisperq und prüfen, ob Hinweis oder Bewerber erscheint)
- [SKIP] T171 J – K5: tools/luac5.1 -v (grund: Werkzeug im Repo (offline))
- [SKIP] T172 J – RM2: Werkzeug nicht in der ZIP (grund: offline (unzip -l))
- [SKIP] T173 J – N8: Offline-Test K2 (grund: offline (test/run_forever95.lua))
- [FEHLER] T185 K – Texte passen (ergebnis: Knöpfe abgeschnitten: 1: settings>gen: Button "wie der Spiel-Client (Deutsc" / "wie der Spiel-Client (Deutsc" · WARNUNG 2 Texte zu lang: progress>achv: Frame "Jeder Hauptberuf auf 300" / "fehlt: Verzauberkunst, Leder"; recruit>texts: EditBox "Danke für dein Interesse an" / "Danke für dein Intere… | erwartet: 0 abgeschnittene Knöpfe)

**Testlauf 0.9.55 · forever 1.60.1 (Interface 16001) · 18.11.2026 05:39 UTC** – OK 317 · FEHLER 0 · übersprungen 23 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Allgemein: 'Bank-Charakter' anhaken, Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
- [CLIENT] T199 B – Verwaltungsknopf an der Gildenseite (anleitung: J drücken: rechts neben dem Gildenfenster steht 'Verwaltung (GuildSentinel)' (ohne Rechte grau); /gs verwaltung öffnet das Fenster; Passwort festlegen und mit falschem/richtigem Passwort entsperren)
- [CLIENT] T191 B – Gilden-Berufsliste im Spiel (anleitung: Mit Gilde einloggen, 5 Minuten warten, /gs protokoll: Zeile 'Gilden-Berufsliste: … Zeilen' zeigt, ob das Spiel die Berufe der Mitglieder liefert; Seite Berufe zeigt dann auch Mitglieder ohne GuildSentinel (nur Stufen))
- [CLIENT] T106 C – echte Kampfsperre (anleitung: Berufe-Seite offen, Kampf beginnen: kein ADDON_ACTION_BLOCKED für GuildSentinel, nach dem Kampf ist der Knopf wieder da)
- [SKIP] T108 D – alter Client (grund: nicht dieser Client)
- [SKIP] T109 D – alter Client (grund: nicht dieser Client)
- [SKIP] T110 D – alter Client (grund: nicht dieser Client)
- [SKIP] T111 D – alter Client (grund: nicht dieser Client)
- [SKIP] T112 D – alter Client (grund: nicht dieser Client)
- [SKIP] T114 D – alter Client (grund: nicht dieser Client)
- [SKIP] T113 D – Berufe klassisch (grund: nicht dieser Client)
- [SKIP] T115 E – Neuinstallation (grund: würde GuildSentinelDB neu anlegen; offline: jeder Lauf in test/ startet ohne GuildSentinelDB)
- [SKIP] T117 E – Migration (grund: offline in test/run_nilglobals.lua (Altlasten) und run_lang.lua (alte Spracheinstellung))
- [SKIP] T119 E – beschädigte Einstellungen (grund: offline in test/run_nilglobals.lua)
- [SKIP] T123 F – alle Schlüssel vorhanden (grund: Client-Sprache ist de (Schlüssel bzw. Locales.lua))
- [CLIENT] T136 G – Guild Roster Manager (anleitung: mit installiertem GRM: Leitung > GRM-Import zeigt Zahlen; ohne: kein Fehler)
- [SKIP] T137 G – ProfessionSentinel (grund: GuildSentinel nutzt keine Schnittstelle von ProfessionSentinel)
- [SKIP] T145 H – Speicher (grund: Messung im Bericht unten (Zeile Speicher, ohne Bereinigung))
- [CLIENT] T189 I – Diagnose-Protokoll im Spiel (anleitung: /gs protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt GuildSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T156 J – P4a: Bewerber-Flüstern im Kampf (grund: wie T85)
- [SKIP] T157 J – P4b: Addon-Nachricht im Kampf (grund: wie T84)
- [SKIP] T158 J – P4c: Abklingzeit im Kampf (grund: wie T86)
- [SKIP] T160 J – P5b: KnowsSpell über C_SpellBook (grund: wie T98/T133)
- [SKIP] T162 J – P6b: ChatFrame_RemoveChannel (grund: wie T101)
- [SKIP] T164 J – Launch-Tag: Interface-Nummer (grund: wie T03)
- [CLIENT] T168 J – K2 im echten Kampf (anleitung: Mitspieler flüstert im Kampf 'gilde'; nach dem Kampf /gs testroutine whisperq und prüfen, ob Hinweis oder Bewerber erscheint)
- [SKIP] T171 J – K5: tools/luac5.1 -v (grund: Werkzeug im Repo (offline))
- [SKIP] T172 J – RM2: Werkzeug nicht in der ZIP (grund: offline (unzip -l))
- [SKIP] T173 J – N8: Offline-Test K2 (grund: offline (test/run_forever95.lua))

**Testlauf 0.9.56 · forever 1.60.1 (Interface 16001) · 18.11.2026 07:32 UTC** – OK 320 · FEHLER 0 · übersprungen 23 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Allgemein: 'Bank-Charakter' anhaken, Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
- [CLIENT] T199 B – Verwaltungsknopf an der Gildenseite (anleitung: J drücken: rechts neben dem Gildenfenster steht 'Verwaltung (GuildSentinel)' (ohne Rechte grau); /gs verwaltung öffnet das Fenster; Passwort festlegen und mit falschem/richtigem Passwort entsperren)
- [CLIENT] T191 B – Gilden-Berufsliste im Spiel (anleitung: Mit Gilde einloggen, 5 Minuten warten, /gs protokoll: Zeile 'Gilden-Berufsliste: … Zeilen' zeigt, ob das Spiel die Berufe der Mitglieder liefert; Seite Berufe zeigt dann auch Mitglieder ohne GuildSentinel (nur Stufen))
- [CLIENT] T106 C – echte Kampfsperre (anleitung: Berufe-Seite offen, Kampf beginnen: kein ADDON_ACTION_BLOCKED für GuildSentinel, nach dem Kampf ist der Knopf wieder da)
- [SKIP] T108 D – alter Client (grund: nicht dieser Client)
- [SKIP] T109 D – alter Client (grund: nicht dieser Client)
- [SKIP] T110 D – alter Client (grund: nicht dieser Client)
- [SKIP] T111 D – alter Client (grund: nicht dieser Client)
- [SKIP] T112 D – alter Client (grund: nicht dieser Client)
- [SKIP] T114 D – alter Client (grund: nicht dieser Client)
- [SKIP] T113 D – Berufe klassisch (grund: nicht dieser Client)
- [SKIP] T115 E – Neuinstallation (grund: würde GuildSentinelDB neu anlegen; offline: jeder Lauf in test/ startet ohne GuildSentinelDB)
- [SKIP] T117 E – Migration (grund: offline in test/run_nilglobals.lua (Altlasten) und run_lang.lua (alte Spracheinstellung))
- [SKIP] T119 E – beschädigte Einstellungen (grund: offline in test/run_nilglobals.lua)
- [SKIP] T123 F – alle Schlüssel vorhanden (grund: Client-Sprache ist de (Schlüssel bzw. Locales.lua))
- [CLIENT] T136 G – Guild Roster Manager (anleitung: mit installiertem GRM: Leitung > GRM-Import zeigt Zahlen; ohne: kein Fehler)
- [SKIP] T137 G – ProfessionSentinel (grund: GuildSentinel nutzt keine Schnittstelle von ProfessionSentinel)
- [SKIP] T145 H – Speicher (grund: Messung im Bericht unten (Zeile Speicher, ohne Bereinigung))
- [CLIENT] T189 I – Diagnose-Protokoll im Spiel (anleitung: /gs protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt GuildSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T156 J – P4a: Bewerber-Flüstern im Kampf (grund: wie T85)
- [SKIP] T157 J – P4b: Addon-Nachricht im Kampf (grund: wie T84)
- [SKIP] T158 J – P4c: Abklingzeit im Kampf (grund: wie T86)
- [SKIP] T160 J – P5b: KnowsSpell über C_SpellBook (grund: wie T98/T133)
- [SKIP] T162 J – P6b: ChatFrame_RemoveChannel (grund: wie T101)
- [SKIP] T164 J – Launch-Tag: Interface-Nummer (grund: wie T03)
- [CLIENT] T168 J – K2 im echten Kampf (anleitung: Mitspieler flüstert im Kampf 'gilde'; nach dem Kampf /gs testroutine whisperq und prüfen, ob Hinweis oder Bewerber erscheint)
- [SKIP] T171 J – K5: tools/luac5.1 -v (grund: Werkzeug im Repo (offline))
- [SKIP] T172 J – RM2: Werkzeug nicht in der ZIP (grund: offline (unzip -l))
- [SKIP] T173 J – N8: Offline-Test K2 (grund: offline (test/run_forever95.lua))

**Fehler im Spiel (letzte 7 Tage)**
- 4× `GS_APPS`: Interface/AddOns/GuildSentinel/Roster.lua:124: attempt to index field 'alts' (a nil value) – Version 0.9.51 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 15:47 UTC
- 1× `ADDON_ACTION_FORBIDDEN`: fn() – Version 0.9.28 · forever 1.60.1 (Interface 16001) · zuletzt 13.11.2026 04:43 UTC

## LevelPilot

**Testlauf 3.12.89 · forever 1.60.1 (Interface 16001) · 17.11.2026 19:12 UTC** – OK 1 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.12.91 · forever 1.60.1 (Interface 16001) · 18.11.2026 05:47 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.12.92 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:05 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.12.93 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:40 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Fehler im Spiel (letzte 7 Tage)**
- 15× `Reise`: Fehler in der Reise: Interface/AddOns/LevelPilot/Virtual.lua:135: attempt to perform indexed assignment on field '?' (a boolean value) – Version 3.12.89 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 19:02 UTC

## ProfessionSentinel

**Testlauf 0.9.13 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:17 UTC** – OK 144 · FEHLER 6 · übersprungen 9 · im Client prüfen 13 · Sandbox OK
- [CLIENT] T06 A – Interface-Nummer akzeptiert (anleitung: Launch: /dump select(4, GetBuildInfo()) – die Nummer muss in allen 4 TOCs stehen (Client 16001))
- [CLIENT] T30 B – Lebenslinien-Widget und Hooks (anleitung: Berufsfenster öffnen, dann /ps testroutine b (Widget automatisch OK))
- [CLIENT] T42 B – Echter Kartenpin (halbautomatisch) (anleitung: Rechtsklick im Panel auf ein fehlendes Rezept mit Händler: Pin muss gesetzt werden, danach selbst entfernen; bestätigen mit /ps testroutine ok T42)
- [CLIENT] T50 B – Favor-Stand (anleitung: Handelslager-Händler öffnen (Favor-Stand unbekannt), dann /ps testroutine b)
- [SKIP] T56 B – Händlergunst in anderen Versionen aus (grund: nur Classic Era / Retail)
- [FEHLER] T63 B – Eingabefenster Aufschlag, Mindestgewinn, Marge (lua: ...face/AddOns/Blizzard_StaticPopup_Game/GameDialog.lua:124: invalid option in `format')
- [CLIENT] T69 B – Rezepte in den Taschen (anleitung: ein Rezept-Item in die Taschen legen, dann /ps testroutine b)
- [CLIENT] T70 B – Anbindung an den AHSentinel-Scan (anleitung: mit AHSentinel einen AH-Scan machen: Rezept-Alarm bzw. Gruppe „alerts“ im Panel erscheint (angemeldet: true))
- [CLIENT] T85 B – Andocken und Hinweis „bester Rezept“ (anleitung: Berufsfenster öffnen (Addons dürfen das nicht selbst), dann /ps testroutine b)
- [SKIP] T108 C – Alter Tooltip-Weg (grund: nur im alten Client prüfbar – siehe T120)
- [CLIENT] T113 C – Panel und Tooltip im echten Kampf (anleitung: Panel offen und Rezept in den Taschen überfahren, dann einen Kampf beginnen und Tooltips ansehen: kein Lua-Fehler, kein ADDON_ACTION_BLOCKED)
- [SKIP] T115 D – Berufe auf dem alten Weg (grund: nur Classic Era)
- [SKIP] T117 D – Händlergunst und Gebühr aus (grund: nur Classic Era)
- [SKIP] T118 D – Reiter-Layout wie früher (grund: nur Classic Era / Retail)
- [SKIP] T119 D – Lebenslinie im Blizzard-Fenster alt (grund: nur Classic Era)
- [SKIP] T120 D – Tooltip-Weg im alten Client (grund: nur Classic Era)
- [SKIP] T121 D – TBC bleibt untätig (grund: kein TBC-Client in diesem Lauf (simuliert in T10/T172))
- [SKIP] T122 D – Retail-Eigenheiten (grund: nur Retail)
- [FEHLER] T132 G – Keine globalen Namen überschrieben (ergebnis: 17 Prüfungen, 1 Fehler: nicht erlaubt: ProfessionSentinelAutoTestReportBg, ProfessionSentinelAutoTestReportCloseButton, ProfessionSentinelAutoTestReportInset, ProfessionSentinelAutoTestReportPortrait, ProfessionSentinelAutoTestReportText, ProfessionSentinelAutoTestReportTitleText, ProfessionSentine… | erwartet: 0 Fehler)
- [CLIENT] T138 G – AHSentinel „Heute tun“ zeigt Herstellungen (anleitung: AHSentinel „Heute tun“ öffnen: Zeilen von ProfessionSentinel erscheinen dort)
- [FEHLER] T139 H – Panel-Aufbau je Ansicht (ergebnis: 6 Ansichten, 6 Fehler: recipes 36.1 ms · langsamste 44.2 ms (Lederverarbeitung) | erwartet: < 16 ms)
- [FEHLER] T140 H – Bestes Rezept bei jedem Berufs-Ereignis (ergebnis: 20.2 ms | erwartet: < 16 ms)
- [FEHLER] T143 H – Teure Rechnungen (ergebnis: 6 Rechnungen, 2 Fehler: AD.Plan 1->300 67.6 ms | erwartet: 0 Fehler)
- [CLIENT] T144 H – Lebenslinie im Blizzard-Fenster (anleitung: Berufsfenster öffnen, dann /ps testroutine h)
- [CLIENT] T169 J – Interface-Nummer nach dem Launch (anleitung: /dump select(4, GetBuildInfo()) – Nummer in allen 4 TOCs (Client 16001))
- [CLIENT] T177 J – Gildenblick bleibt leer, solange RaidMaster in Forever nichts einliest (anleitung: automatisch OK; nach dem RaidMaster-Fix: Gildenblick zeigt Einträge)
- [CLIENT] T186 B – Minimap-Button im Spiel (anleitung: Buch-Symbol an der Minimap sichtbar, Tooltip in der Sprache des Clients, Ziehen verschiebt ihn, nach /reload am selben Ort, Linksklick wie /ps, Rechtsklick listet die Optionen; bestätigen mit /ps testroutine ok T186)
- [FEHLER] T145 H – Speicher (ergebnis: 20× Refresh: +0 KB · nach dem Lauf: +1230 KB | erwartet: < 256 KB / < 1024 KB)

**Testlauf 0.9.28 · forever 1.60.1 (Interface 16001) · 09.11.2026 06:57 UTC** – OK 5 · FEHLER 2 · übersprungen 1 · im Client prüfen 0
- [SKIP] S5 S – Gleiche AH-Gebühr wie AHSentinel (grund: 5 Rezepte im Panel anklicken (Berufsfenster offen))
- [FEHLER] S7 S – Kein Neuaufbau-Sturm beim Herstellen (ergebnis: 0.2 Aufbau/s, 3 LANGSAM | erwartet: ≤ 2/s, 0 LANGSAM)
- [FEHLER] S8 S – Oberflächen-Prüfung (Bereich K) (ergebnis: CheckButton verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; CheckButton verdeckt Button; Button verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; Button… | erwartet: keine)

**Testlauf 0.9.66 · forever 1.60.1 (Interface 16001) · 17.11.2026 19:22 UTC** – OK 1 · FEHLER 1 · übersprungen 8 · im Client prüfen 0
- [FEHLER] S2 S – Fertigkeit und Plan-Start (ergebnis: Fertigkeit 0 | erwartet: > 0)
- [SKIP] S3 S – Zähler sinkt nach einem Skillpunkt (grund: herstellen, bis ein Skillpunkt kommt)
- [SKIP] S4 S – Andocken ohne Überlappen (grund: Rezept wählen, damit das AHSentinel-Gewinn-Fenster erscheint)
- [SKIP] S5 S – Gleiche AH-Gebühr wie AHSentinel (grund: 5 Rezepte im Panel anklicken (Berufsfenster offen))
- [SKIP] S6 S – Rangliste Leveln sortiert (grund: Reiter „Rangliste“ öffnen)
- [SKIP] S7 S – Kein Neuaufbau-Sturm beim Herstellen (grund: 5 Gegenstände hintereinander herstellen)
- [SKIP] S8 S – Oberflächen-Prüfung (Bereich K) (grund: Berufsfenster mit Panel öffnen)
- [SKIP] S9 S – Gekaufte Menge = eingegebene Menge (grund: beim Händler: in der Einkaufsliste eine Menge eingeben und „Kaufen“ klicken)
- [SKIP] S10 S – Shift+Klick öffnet das Mengenfenster (grund: beim Händler: Shift+Klick auf eine Ware, dann noch einmal mit offener Chat-Eingabe)

**Testlauf 0.9.68 · forever 1.60.1 (Interface 16001) · 18.11.2026 07:50 UTC** – OK 1 · FEHLER 1 · übersprungen 8 · im Client prüfen 0
- [FEHLER] S2 S – Fertigkeit und Plan-Start (ergebnis: Fertigkeit 0 | erwartet: > 0)
- [SKIP] S3 S – Zähler sinkt nach einem Skillpunkt (grund: herstellen, bis ein Skillpunkt kommt)
- [SKIP] S4 S – Andocken ohne Überlappen (grund: Rezept wählen, damit das AHSentinel-Gewinn-Fenster erscheint)
- [SKIP] S5 S – Gleiche AH-Gebühr wie AHSentinel (grund: 5 Rezepte im Panel anklicken (Berufsfenster offen))
- [SKIP] S6 S – Rangliste Leveln sortiert (grund: Reiter „Rangliste“ öffnen)
- [SKIP] S7 S – Kein Neuaufbau-Sturm beim Herstellen (grund: 5 Gegenstände hintereinander herstellen)
- [SKIP] S8 S – Oberflächen-Prüfung (Bereich K) (grund: Berufsfenster mit Panel öffnen)
- [SKIP] S9 S – Gekaufte Menge = eingegebene Menge (grund: beim Händler: in der Einkaufsliste eine Menge eingeben und „Kaufen“ klicken)
- [SKIP] S10 S – Shift+Klick öffnet das Mengenfenster (grund: beim Händler: Shift+Klick auf eine Ware, dann noch einmal mit offener Chat-Eingabe)

**Fehler im Spiel (letzte 7 Tage)**
- 5× `AHSentinel:On`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:161: attempt to concatenate local 'line' (a nil value) – Version 0.9.67 · forever 1.60.1 (Interface 16001) · zuletzt 18.11.2026 05:33 UTC
- 1× `Aufgabe t279`: attempt to yield across metamethod/C-call boundary – Version 0.9.66 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 19:23 UTC
- 1× `ADDON_ACTION_BLOCKED`: UNKNOWN() – Version 0.9.66 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 19:18 UTC
- 1× `Aufgabe t143`: attempt to yield across metamethod/C-call boundary – Version 0.9.66 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 19:22 UTC

## RaidMaster

**Testlauf 3.0.31 · forever 1.60.1 (Interface 16001) · 17.11.2026 18:38 UTC** – OK 134 · FEHLER 1 · übersprungen 16 · im Client prüfen 10 · Sandbox OK
- [SKIP] T06 A – Fähigkeiten folgen der Weiche (grund: Caps nur beim Laden berechnet)
- [SKIP] T35b B – Berufe: Fenster wird eingelesen (grund: wartet auf Fenster: Berufe – passiert von selbst, wenn du das nächste Mal ein Berufsfenster öffnest)
- [SKIP] T36b B – Bank-Charakter: Bank wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [SKIP] T36c B – Bank-Charakter: Post wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [SKIP] T43 B – Test-Werkzeug selbst (ony) (grund: Beute geladen 10/26; im Durchlauf 0 Items behandelt (0 Versteigerung, 0 andere Regel), 0 ohne Daten – beim nächsten Lauf wieder)
- [CLIENT] T51b C – Absender von Addon-Nachrichten im Kampf geschützt? (anleitung: Forever, im Kampf mit Mitspieler: /rm sync – kommt keine Lua-Meldung, ist alles gut)
- [CLIENT] T54b C – Systemmeldung mit geschütztem Text (anleitung: Forever, im Kampf jemanden einladen lassen: kommt keine Lua-Meldung, ist alles gut (echte geschützte Strings lassen sich nicht nachstellen))
- [SKIP] T71 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T72 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T73 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T74 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T75 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T91 F – Formatplatzhalter (grund: offline geprüft (Lua 5.1 mit lupa))
- [CLIENT] T92 F – Jede Sprache einmal aktiv (anleitung: einmal mit englischem Client /rmtest testroutine F)
- [CLIENT] T103 G – DBM und BigWigs (anleitung: Pull-Timer aus der Boss-Leiste: Balken bei DBM/BigWigs sichtbar?)
- [CLIENT] T104 G – BugSack/BugGrabber (anleitung: mit BugSack: /rmtest testroutine I – Testfehler in BugSack und Diagnose?)
- [CLIENT] T133b J – Mouseover-Tasten und Symbol-Leiste im echten Kampf (anleitung: Forever: Mob im Kampf per RaidMaster-Taste (Mouseover) und per Klick auf die Symbol-Leiste markieren, Rechtsklick entfernt, 'Alle aus' – Symbol da, Fehlerliste leer, kein 'Aktion blockiert'?)
- [CLIENT] T135 J – Skillungen in Forever (anleitung: /dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten)
- [CLIENT] T136b J – Plündermeister vorhanden (anleitung: /dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod())
- [CLIENT] T146 J – Bereitschafts-Check in alten Clients (anleitung: Era/Anniversary mit Fläschchen: /rm bereit – erkannt?)
- [SKIP] T147 J – Berufe-Knopf übersetzt (grund: offline geprüft (Locales))
- [CLIENT] T152 J – Berufe-Knopf im Client (anleitung: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [SKIP] T156 K – Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern (grund: nichts geprüft (kein sichtbares Fenster mit messbaren Rechtecken))
- [FEHLER] T158 K – Beschriftungen von Knöpfen nicht abgeschnitten (ergebnis: lboss: Hauptfenster: 'Golemagg der Verbrenner |TInterface\TargetingFrame\UI-RaidTargetingIcon_8:0|t' Beschriftung abgeschnitten; discord: Hauptfenster: '7. Vor dem Raid: Anmeldungen holen' Beschriftung abgeschnitten · geprüft 2358 · Hinweise: Bereitschaft: Text gekürzt bei Button; Bereitschaft: … | erwartet: keine)
- [SKIP] T90 F – Fehlende Übersetzungen (grund: Grundsprache)
- [SKIP] T184 F – Platzhalter der Übersetzungen (grund: Grundsprache)
- [SKIP] T70 D – Ganze Routine im alten Client (grund: nur im alten Client (Era/TBC): dort /rmtest testroutine)

**Testlauf 3.0.30 · forever 1.60.1 (Interface 16001) · 18.11.2026 05:40 UTC** – OK 131 · FEHLER 4 · übersprungen 11 · im Client prüfen 12 · Sandbox OK
- [SKIP] T06 A – Fähigkeiten folgen der Weiche (grund: Caps nur beim Laden berechnet)
- [CLIENT] T35b B – Berufe (Fenster echt öffnen) (anleitung: siehe T152: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [CLIENT] T36b B – Gildenbank echt (anleitung: Bank-Charakter: Bank öffnen, Post öffnen, dann /rm bank – Bestand > 0 Einträge?)
- [FEHLER] T43 B – Test-Werkzeug selbst (ony) (ergebnis: kein Item vergeben (Beute geladen 10/26) | erwartet: >= 1)
- [CLIENT] T51b C – Absender von Addon-Nachrichten im Kampf geschützt? (anleitung: Forever, im Kampf mit Mitspieler: /rm sync – kommt keine Lua-Meldung, ist alles gut)
- [CLIENT] T54b C – Systemmeldung mit geschütztem Text (anleitung: Forever, im Kampf jemanden einladen lassen: kommt keine Lua-Meldung, ist alles gut (echte geschützte Strings lassen sich nicht nachstellen))
- [SKIP] T71 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T72 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T73 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T74 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T75 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T91 F – Formatplatzhalter (grund: offline geprüft (Lua 5.1 mit lupa))
- [CLIENT] T92 F – Jede Sprache einmal aktiv (anleitung: einmal mit englischem Client /rmtest testroutine F)
- [CLIENT] T103 G – DBM und BigWigs (anleitung: Pull-Timer aus der Boss-Leiste: Balken bei DBM/BigWigs sichtbar?)
- [CLIENT] T104 G – BugSack/BugGrabber (anleitung: mit BugSack: /rmtest testroutine I – Testfehler in BugSack und Diagnose?)
- [CLIENT] T133b J – Mouseover-Tasten und Symbol-Leiste im echten Kampf (anleitung: Forever: Mob im Kampf per RaidMaster-Taste (Mouseover) und per Klick auf die Symbol-Leiste markieren, Rechtsklick entfernt, 'Alle aus' – Symbol da, Fehlerliste leer, kein 'Aktion blockiert'?)
- [CLIENT] T135 J – Skillungen in Forever (anleitung: /dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten)
- [CLIENT] T136b J – Plündermeister vorhanden (anleitung: /dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod())
- [CLIENT] T146 J – Bereitschafts-Check in alten Clients (anleitung: Era/Anniversary mit Fläschchen: /rm bereit – erkannt?)
- [SKIP] T147 J – Berufe-Knopf übersetzt (grund: offline geprüft (Locales))
- [CLIENT] T152 J – Berufe-Knopf im Client (anleitung: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [FEHLER] T169 J – T-BL4 Chatfeld wird nie beschrieben (ergebnis: Lua-Fehler | erwartet: kein Fehler)
- [FEHLER] T155 K – Eigene Tooltips verdecken keine Knöpfe (ergebnis: dkp: Markierungsleiste: Button verdeckt Button; auction: Markierungsleiste: Button verdeckt Button; loot: Markierungsleiste: Button verdeckt Button; log: Markierungsleiste: Button verdeckt Button; raid: Markierungsleiste: Button verdeckt Button; signup: Markierungsleiste: Button verdeckt Button; pug… | erwartet: keine)
- [FEHLER] T156 K – Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern (ergebnis: dkp: Hauptfenster überdeckt Pfeil (LevelPilot); dkp: Bereitschaft überdeckt Pfeil (LevelPilot); auction: Hauptfenster überdeckt Pfeil (LevelPilot); auction: Bereitschaft überdeckt Pfeil (LevelPilot); loot: Hauptfenster überdeckt Pfeil (LevelPilot); loot: Bereitschaft überdeckt Pfeil (LevelPilo… | erwartet: keine)
- [SKIP] T90 F – Fehlende Übersetzungen (grund: Grundsprache)
- [SKIP] T184 F – Platzhalter der Übersetzungen (grund: Grundsprache)
- [SKIP] T70 D – Ganze Routine im alten Client (grund: nur im alten Client (Era/TBC): dort /rmtest testroutine)

**Testlauf 3.0.34 · forever 1.60.1 (Interface 16001) · 18.11.2026 07:46 UTC** – OK 0 · FEHLER 1 · übersprungen 0 · im Client prüfen 0
- [FEHLER] T35b B – Berufe: Fenster wird eingelesen (nachgeholt) (ergebnis: nach dem Öffnen nicht eingelesen | erwartet: Berufe-Daten neu)

**Testlauf 3.0.35 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:44 UTC** – OK 138 · FEHLER 0 · übersprungen 15 · im Client prüfen 10 · Sandbox OK
- [SKIP] T06 A – Fähigkeiten folgen der Weiche (grund: Caps nur beim Laden berechnet)
- [SKIP] T35b B – Berufe: Fenster wird eingelesen (grund: wartet auf Fenster: Berufe – passiert von selbst, wenn du das nächste Mal ein Berufsfenster öffnest)
- [SKIP] T36b B – Bank-Charakter: Bank wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [SKIP] T36c B – Bank-Charakter: Post wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [SKIP] T43 B – Test-Werkzeug selbst (ony) (grund: Beute geladen 10/26, davon versteigerbar 0 – beim nächsten Lauf wieder)
- [CLIENT] T51b C – Absender von Addon-Nachrichten im Kampf geschützt? (anleitung: Forever, im Kampf mit Mitspieler: /rm sync – kommt keine Lua-Meldung, ist alles gut)
- [CLIENT] T54b C – Systemmeldung mit geschütztem Text (anleitung: Forever, im Kampf jemanden einladen lassen: kommt keine Lua-Meldung, ist alles gut (echte geschützte Strings lassen sich nicht nachstellen))
- [SKIP] T71 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T72 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T73 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T74 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T75 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T91 F – Formatplatzhalter (grund: offline geprüft (Lua 5.1 mit lupa))
- [CLIENT] T92 F – Jede Sprache einmal aktiv (anleitung: einmal mit englischem Client /rmtest testroutine F)
- [CLIENT] T103 G – DBM und BigWigs (anleitung: Pull-Timer aus der Boss-Leiste: Balken bei DBM/BigWigs sichtbar?)
- [CLIENT] T104 G – BugSack/BugGrabber (anleitung: mit BugSack: /rmtest testroutine I – Testfehler in BugSack und Diagnose?)
- [CLIENT] T133b J – Mouseover-Tasten und Symbol-Leiste im echten Kampf (anleitung: Forever: Mob im Kampf per RaidMaster-Taste (Mouseover) und per Klick auf die Symbol-Leiste markieren, Rechtsklick entfernt, 'Alle aus' – Symbol da, Fehlerliste leer, kein 'Aktion blockiert'?)
- [CLIENT] T135 J – Skillungen in Forever (anleitung: /dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten)
- [CLIENT] T136b J – Plündermeister vorhanden (anleitung: /dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod())
- [CLIENT] T146 J – Bereitschafts-Check in alten Clients (anleitung: Era/Anniversary mit Fläschchen: /rm bereit – erkannt?)
- [SKIP] T147 J – Berufe-Knopf übersetzt (grund: offline geprüft (Locales))
- [CLIENT] T152 J – Berufe-Knopf im Client (anleitung: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [SKIP] T90 F – Fehlende Übersetzungen (grund: Grundsprache)
- [SKIP] T184 F – Platzhalter der Übersetzungen (grund: Grundsprache)
- [SKIP] T70 D – Ganze Routine im alten Client (grund: nur im alten Client (Era/TBC): dort /rmtest testroutine)

## ThreatSentinel

**Testlauf 2.5.16 · forever 1.60.1 (Interface 16001) · 17.11.2026 16:00 UTC** – OK 272 · FEHLER 4 · übersprungen 10 · im Client prüfen 15 · Sandbox OK
- [CLIENT] T11 A – Interface-Nummer des Clients in der .toc (anleitung: Interface steht in der Kopfzeile des Berichts; die Prüf-Sitzung vergleicht sie mit ## Interface (am Launch-Tag /dump select(4, GetBuildInfo())))
- [CLIENT] T46 B – Bedrohung prüfen – im Kampf (anleitung: Mob angreifen, im Kampf /ts bedrohung: Status und Prozent (oder 'geschützt') erscheinen, kein Lua-Fehler)
- [CLIENT] T109 C – Keine geschützten Aktionen im Kampf (anleitung: Im Kampf: Einstellungen öffnen (Hinweis 'nicht im Kampf'), /ts move (verweigert); danach /ts test > Bericht: Blocked: none)
- [CLIENT] T110 C – Plaketten im Kampf in ANZEIGE/AUS (anleitung: Forever, Modus ANZEIGE: Pull mit 3+ Mobs – nichts leuchtet, Plaketten unverändert; nach dem Kampf wieder normal)
- [SKIP] T112 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T113 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T114 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T115 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T116 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T117 D – Gegenprobe im echten Spiel (grund: nur Classic Era / TBC)
- [SKIP] T126 F – Im Code benutzte Schlüssel (grund: vor dem Push per Skript geprüft (manuell))
- [CLIENT] T128 F – Andere Sprache aktivieren (anleitung: /ts testroutine sprache, dann /reload, dann /ts testroutine f (Popups und Tastenbelegungs-Namen bleiben in der Spielsprache))
- [SKIP] T134 G – Schnittstellen zu den anderen Addons (grund: keine Schnittstelle)
- [CLIENT] T135 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: Mit RaidMaster, GuildSentinel, BuffSentinel, ProfessionSentinel laden, /reload, /gsgame: eine Zeile, Version 3; /ts testroutine g)
- [CLIENT] T188 I – Diagnose-Protokoll im Spiel (anleitung: /ts protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt ThreatSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T147 I – Lua-Fehler ausserhalb von pcall (grund: würde einen echten Fehler im Fehlerfenster/BugSack des Spielers auslösen; GoldSentinelTest.TrackErrors ist angemeldet (siehe Core.lua))
- [CLIENT] T148 J – Kein Ersatz über das Ziel des Mobs (modern) (anleitung: Forever: Mob ohne Bedrohungsdaten bleibt IDLE (Diagnose 'Bedrohung am Ziel'), kein Leuchten)
- [CLIENT] T149 J – Kein stilles IDLE bei geschützten Werten (anleitung: Forever, erster Kampf: /ts bedrohung zeigt 'geschützt', Hinweis 1x)
- [CLIENT] T154 J – Taint im Modus VOLL (anleitung: Pull mit 3+ Mobs im Modus VOLL, danach /ts test > Bericht: 'Blocked: none'; kein 'ThreatSentinel hat eine Aktion blockiert')
- [CLIENT] T157 J – Erkennung einmal pro Kampf, Zustand gespeichert (anleitung: Forever: zwei Kämpfe hintereinander, danach /ts bedrohung: 'zuletzt erkannt' mit Datum und Build)
- [CLIENT] T174 J – UnitIsUnit nur über ns:SameUnit (anleitung: Forever, Gruppe im Kampf: kein Lua-Fehler (Testzentrale-Diagnose 'Fehler: 0'))
- [CLIENT] T176b J – Alter Client: Kampf in der Gruppe (anleitung: Classic Era und TBC Anniversary: Schadens-/Heilmeter zählt, widerstandener Spott wird gemeldet, kein 'Addon geblockt' – Ergebnis dem Nutzer melden)
- [CLIENT] T177 J – Launch-Tag: Interface-Nummer und erster Kampf (anleitung: /dump select(4, GetBuildInfo()); im ersten Kampf /ts bedrohung -> Modus im Bericht)
- [SKIP] T178 J – Lua-Syntaxprüfung (grund: vor dem Push mit addon_check.py (manuell))
- [FEHLER] T181 K – Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern (ergebnis: Testzentrale überdeckt Pfeil (LevelPilot) · geprüft 1 | erwartet: keine)
- [FEHLER] T-K2 K – Testzentrale weicht sichtbaren Fenstern anderer GoldSentinel-Addons aus (ergebnis: verschoben true, Überdeckung 10204.191215168 | erwartet: verschoben true, Überdeckung 0)
- [CLIENT] T186 K – Oberfläche mit offenen Blizzard-Fenstern (anleitung: Charakterfenster, Karte, Händler oder Post öffnen, dazu Testzentrale und Einstellungen; dann /ts testroutine k: T181 ohne Überlappen)
- [FEHLER] TU1-L04t U – TU1 Schlachtzug 40 mit 40 Mobs: ein Durchlauf < 8 ms (ergebnis: 10.30 ms | erwartet: < 8 ms)
- [FEHLER] TU6-R1 U – TU6 Regressionen: jeder Befund hat seinen Test, der Test lief (ergebnis: Regressionen: 49 von 49 vorhanden, nur im Client: T110 T128, Test FEHLER: 2.5.2 T180/T181 Rahmenname, Testzentrale über Blizzard-Fenstern; 2.5.8-1 T-K2 im Client immer FEHLER | erwartet: alle vorhanden, alle OK)

**Testlauf 2.5.19 · forever 1.60.1 (Interface 16001) · 18.11.2026 05:48 UTC** – OK 0 · FEHLER 1 · übersprungen 0 · im Client prüfen 0
- [FEHLER] T186 K – Oberfläche mit offenen Blizzard-Fenstern (nachgeholt bei CharacterFrame) (ergebnis: Testzentrale überdeckt Kopierfenster (LevelPilot); Einstellungen überdeckt Kopierfenster (LevelPilot) · geprüft 4 | erwartet: keine, geprüft > 0)

**Testlauf 2.5.20 · forever 1.60.1 (Interface 16001) · 18.11.2026 07:46 UTC** – OK 0 · FEHLER 1 · übersprungen 0 · im Client prüfen 0
- [FEHLER] T186 K – Oberfläche mit offenen Blizzard-Fenstern (nachgeholt bei ProfessionsFrame) (ergebnis: Testzentrale überdeckt ProfessionSentinel-Panel (ProfessionSentinel); Testzentrale überdeckt AHAnalyzerProSelfTest (AHSentinel); Einstellungen überdeckt ProfessionSentinel-Panel (ProfessionSentinel); Einstellungen überdeckt AHAnalyzerProSelfTest (AHSentinel) · geprüft 6 | erwartet: keine, geprüft > 0)

**Testlauf 2.5.21 · forever 1.60.1 (Interface 16001) · 18.11.2026 08:44 UTC** – OK 301 · FEHLER 0 · übersprungen 11 · im Client prüfen 14 · Sandbox OK
- [CLIENT] T11 A – Interface-Nummer des Clients in der .toc (anleitung: Interface steht in der Kopfzeile des Berichts; die Prüf-Sitzung vergleicht sie mit ## Interface (am Launch-Tag /dump select(4, GetBuildInfo())))
- [CLIENT] T46 B – Bedrohung prüfen – im Kampf (anleitung: Mob angreifen, im Kampf /ts bedrohung: Status und Prozent (oder 'geschützt') erscheinen, kein Lua-Fehler)
- [CLIENT] T109 C – Keine geschützten Aktionen im Kampf (anleitung: Im Kampf: Einstellungen öffnen (Hinweis 'nicht im Kampf'), /ts move (verweigert); danach /ts test > Bericht: Blocked: none)
- [CLIENT] T110 C – Plaketten im Kampf in ANZEIGE/AUS (anleitung: Forever, Modus ANZEIGE: Pull mit 3+ Mobs – nichts leuchtet, Plaketten unverändert; nach dem Kampf wieder normal)
- [SKIP] T112 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T113 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T114 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T115 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T116 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T117 D – Gegenprobe im echten Spiel (grund: nur Classic Era / TBC)
- [SKIP] T126 F – Im Code benutzte Schlüssel (grund: vor dem Push per Skript geprüft (manuell))
- [CLIENT] T128 F – Andere Sprache aktivieren (anleitung: /ts testroutine sprache, dann /reload, dann /ts testroutine f (Popups und Tastenbelegungs-Namen bleiben in der Spielsprache))
- [SKIP] T134 G – Schnittstellen zu den anderen Addons (grund: keine Schnittstelle)
- [CLIENT] T135 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: Mit RaidMaster, GuildSentinel, BuffSentinel, ProfessionSentinel laden, /reload, /gsgame: eine Zeile, Version 3; /ts testroutine g)
- [CLIENT] T188 I – Diagnose-Protokoll im Spiel (anleitung: /ts protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt ThreatSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables und geht mit dem Uploader nach #testberichte)
- [SKIP] T147 I – Lua-Fehler ausserhalb von pcall (grund: würde einen echten Fehler im Fehlerfenster/BugSack des Spielers auslösen; GoldSentinelTest.TrackErrors ist angemeldet (siehe Core.lua))
- [CLIENT] T148 J – Kein Ersatz über das Ziel des Mobs (modern) (anleitung: Forever: Mob ohne Bedrohungsdaten bleibt IDLE (Diagnose 'Bedrohung am Ziel'), kein Leuchten)
- [CLIENT] T149 J – Kein stilles IDLE bei geschützten Werten (anleitung: Forever, erster Kampf: /ts bedrohung zeigt 'geschützt', Hinweis 1x)
- [CLIENT] T154 J – Taint im Modus VOLL (anleitung: Pull mit 3+ Mobs im Modus VOLL, danach /ts test > Bericht: 'Blocked: none'; kein 'ThreatSentinel hat eine Aktion blockiert')
- [CLIENT] T157 J – Erkennung einmal pro Kampf, Zustand gespeichert (anleitung: Forever: zwei Kämpfe hintereinander, danach /ts bedrohung: 'zuletzt erkannt' mit Datum und Build)
- [CLIENT] T174 J – UnitIsUnit nur über ns:SameUnit (anleitung: Forever, Gruppe im Kampf: kein Lua-Fehler (Testzentrale-Diagnose 'Fehler: 0'))
- [CLIENT] T176b J – Alter Client: Kampf in der Gruppe (anleitung: Classic Era und TBC Anniversary: Schadens-/Heilmeter zählt, widerstandener Spott wird gemeldet, kein 'Addon geblockt' – Ergebnis dem Nutzer melden)
- [CLIENT] T177 J – Launch-Tag: Interface-Nummer und erster Kampf (anleitung: /dump select(4, GetBuildInfo()); im ersten Kampf /ts bedrohung -> Modus im Bericht)
- [SKIP] T178 J – Lua-Syntaxprüfung (grund: vor dem Push mit addon_check.py (manuell))
- [SKIP] T186 K – Oberfläche mit offenen Blizzard-Fenstern (grund: wartet auf ein Spielfenster – läuft nach dem Lauf von selbst (siehe Zusammenfassung))
