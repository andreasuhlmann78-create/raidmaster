# Testberichte der GoldSentinel-Addons

Ausgewertet: 2026-11-20 16:38 UTC

Weg: Addon -> SavedVariables -> RaidMasterUploader -> Discord #testberichte -> hier. Neue Berichte kommen beim nächsten /reload oder Ausloggen und dem nächsten Lauf des Uploaders.

| Addon | letzter Testlauf | Version | Client | OK | FEHLER | übersprungen | im Client prüfen | Fehler im Spiel (7 Tage) |
|---|---|---|---|---|---|---|---|---|
| AHSentinel | 20.11.2026 07:53 UTC | 0.65.355 | forever 1.60.1 (Interface 16001) | 2 | 4 | 3 | 0 | 33 |
| BuffSentinel | 18.11.2026 18:19 UTC | 0.9.60 | forever 1.60.1 (Interface 16001) | 218 | 2 | 11 | 10 | 307 |
| GuildSentinel | 18.11.2026 18:20 UTC | 0.9.58 | forever 1.60.1 (Interface 16001) | 329 | 0 | 24 | 8 | 4 |
| LevelPilot | 20.11.2026 06:31 UTC | 3.13.5 | forever 1.60.1 (Interface 16001) | 11 | 0 | 0 | 0 | 15 |
| ProfessionSentinel | 18.11.2026 18:23 UTC | 0.9.74 | forever 1.60.1 (Interface 16001) | 1 | 1 | 8 | 0 | 8 |
| RaidMaster | 18.11.2026 18:21 UTC | 3.0.40 | forever 1.60.1 (Interface 16001) | 0 | 1 | 0 | 0 | 0 |
| ThreatSentinel | 18.11.2026 12:49 UTC | 2.5.23 | forever 1.60.1 (Interface 16001) | 0 | 1 | 0 | 0 | 0 |

## Diagnose-Protokolle (GSDIAG1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| AHSentinel | 187 | `testberichte/diagnose/AHSentinel/0.65.355-91d1d0846660.txt` |
| BuffSentinel | 79 | `testberichte/diagnose/BuffSentinel/0.9.60-fb522145c40a.txt` |
| GSMesstest | 20 | `testberichte/diagnose/GSMesstest/5.1-f65d607ab777.txt` |
| GSSniperLog | 22 | `testberichte/diagnose/GSSniperLog/1.7-f8198d5ac74a.txt` |
| GuildSentinel | 192 | `testberichte/diagnose/GuildSentinel/0.9.58-e52bcbc311ff.txt` |
| LevelPilot | 86 | `testberichte/diagnose/LevelPilot/3.13.6-c9e0a5d8b2da.txt` |
| ProfessionSentinel | 171 | `testberichte/diagnose/ProfessionSentinel/0.9.74-f850c0c0007b.txt` |
| ThreatSentinel | 165 | `testberichte/diagnose/ThreatSentinel/2.5.23-e61faba6e4d4.txt` |

## Wegdaten (GSWEGE1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| LevelPilot | 246 | `testberichte/wege/LevelPilot/LevelPilot-wege-1795190036-c407b7.json` |

## AHSentinel

**Testlauf 0.65.352 · forever 1.60.1 (Interface 16001) · 19.11.2026 11:02 UTC** – OK 2 · FEHLER 4 · übersprungen 3 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 947 OK, 2 FEHLER, 31 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 6 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (ergebnis:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): FEHLER – 24 OK, 2 FEHLER, 6 übersprungen, Sandbox OK)
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 67 OK, 1 FEHLER, 3 übersprungen, Sandbox OK)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus) (Server-Abstand noch 15 Min.))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Testlauf 0.65.353 · forever 1.60.1 (Interface 16001) · 19.11.2026 15:42 UTC** – OK 1 · FEHLER 2 · übersprungen 6 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 933 OK, 1 FEHLER, 46 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 6 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [SKIP] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (grund:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): noch offen – passiert von selbst beim nächsten Öffnen des Auktionshauses)
- [SKIP] ALLES-5 ALLES – Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND) (grund:   5. Wächter 10 Min.: Rechenzeit je Bild und Hürden (WAECHTER-LAST, WAECHTER-FUND): noch offen – passiert von selbst beim nächsten Öffnen des Auktionshauses)
- [SKIP] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (grund:   6. Prüfungen am offenen Auktionshaus: noch offen – passiert von selbst beim nächsten Öffnen des Auktionshauses)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Testlauf 0.65.354 · forever 1.60.1 (Interface 16001) · 20.11.2026 06:23 UTC** – OK 2 · FEHLER 4 · übersprungen 3 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 949 OK, 1 FEHLER, 31 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 5 OK, 2 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (ergebnis:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): FEHLER – 24 OK, 2 FEHLER, 6 übersprungen, Sandbox OK)
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 65 OK, 2 FEHLER, 4 übersprungen, Sandbox OK)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus) (Server-Abstand noch 15 Min.))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Testlauf 0.65.355 · forever 1.60.1 (Interface 16001) · 20.11.2026 07:53 UTC** – OK 2 · FEHLER 4 · übersprungen 3 · im Client prüfen 0
- [FEHLER] ALLES-1 ALLES – Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1) (ergebnis:   1. Automatische Prüfungen (Regeln, Marktlagen-Nachbau TU1): FEHLER – 949 OK, 1 FEHLER, 31 übersprungen, Sandbox OK)
- [FEHLER] ALLES-2 ALLES – Oberflächen-Prüfung (alle Reiter) (ergebnis:   2. Oberflächen-Prüfung (alle Reiter): FEHLER – 6 OK, 1 FEHLER, 0 übersprungen, Sandbox OK)
- [FEHLER] ALLES-4 ALLES – Sniper-Testroutine S1–S13 (ohne echten Kauf) (ergebnis:   4. Sniper-Testroutine S1–S13 (ohne echten Kauf): FEHLER – 24 OK, 2 FEHLER, 6 übersprungen, Sandbox OK)
- [FEHLER] ALLES-6 ALLES – Prüfungen am offenen Auktionshaus (ergebnis:   6. Prüfungen am offenen Auktionshaus: FEHLER – 65 OK, 2 FEHLER, 4 übersprungen, Sandbox OK)
- [SKIP] ALLES-7 ALLES – Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN) (grund:   7. Vollscan zweimal: bleibender Speicher und längste Lücke (VOLLSCAN): noch offen – passiert von selbst beim nächsten Schnell-Vollscan (Entwicklermodus) (Server-Abstand noch 15 Min.))
- [SKIP] ALLES-8 ALLES – Prüfungen am Berufsfenster (grund:   8. Prüfungen am Berufsfenster: noch offen – passiert von selbst beim nächsten Öffnen eines Berufsfensters)
- [SKIP] ALLES-9 ALLES – Prüfungen am Händler (grund:   9. Prüfungen am Händler: noch offen – passiert von selbst beim nächsten Händler-Besuch)

**Fehler im Spiel (letzte 7 Tage)**
- 25× `ADDON_ACTION_BLOCKED`: UNKNOWN() – Version 0.65.182, 0.65.189, 0.65.194, 0.65.196, 0.65.203 · forever 1.60.1 (Interface 16001) · zuletzt 15.11.2026 18:13 UTC
- 1× `Job:craft-top`: Interface/AddOns/AHSentinel/Crafting.lua:515: attempt to index field '?' (a nil value) – Version 0.65.138 · forever 1.60.1 (Interface 16001) · zuletzt 14.11.2026 06:53 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/UI_Main.lua:1303: script ran too long – Version 0.65.260 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 07:18 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1400: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:43 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1402: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:44 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/Ledger.lua:1686: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:44 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/Disenchant.lua:327: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:45 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/AHAnalyzerPro.lua:1801: script ran too long – Version 0.65.278 · forever 1.60.1 (Interface 16001) · zuletzt 16.11.2026 18:43 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/UI_Main.lua:1298: script ran too long – Version 0.65.315 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 11:24 UTC

## BuffSentinel

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

**Testlauf 0.9.56 · forever 1.60.1 (Interface 16001) · 18.11.2026 09:10 UTC** – OK 214 · FEHLER 0 · übersprungen 11 · im Client prüfen 10 · Sandbox OK
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
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T147 J – Diagnose-Protokoll im Spiel (anleitung: /bsen protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt BuffSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')

**Testlauf 0.9.59 · forever 1.60.1 (Interface 16001) · 18.11.2026 12:42 UTC** – OK 220 · FEHLER 0 · übersprungen 11 · im Client prüfen 10 · Sandbox OK
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
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T147 J – Diagnose-Protokoll im Spiel (anleitung: /bsen protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt BuffSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')

**Testlauf 0.9.60 · forever 1.60.1 (Interface 16001) · 18.11.2026 18:19 UTC** – OK 218 · FEHLER 2 · übersprungen 11 · im Client prüfen 10 · Sandbox OK
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
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T147 J – Diagnose-Protokoll im Spiel (anleitung: /bsen protokoll öffnet ein Fenster mit markierbarem Text; nach /reload liegt BuffSentinelDB.diagExport (beginnt mit GSDIAG1) in den SavedVariables)
- [FEHLER] T149 J – Schwebende Anzeigen nicht in der gemeinsamen Fensterliste, leere Anker klein (ergebnis: ja/ja/ja/ja/nein)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')
- [FEHLER] T162 Q – Regressionen: jeder Befund hat einen Test, der gelaufen ist (ergebnis: Regressionen: 30 von 30 vorhanden · FEHLER: ANK Anker A1-A3 (10.11.))

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

**Testlauf 0.9.57 · forever 1.60.1 (Interface 16001) · 18.11.2026 12:44 UTC** – OK 326 · FEHLER 1 · übersprungen 23 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Optionen > Daten & Abgleich: 'Bank-Charakter' auf 'an', Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
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
- [FEHLER] T138 H – Roster:Scan mit 500 Mitgliedern (ergebnis: 16.2 ms | erwartet: < 16 ms)
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

**Testlauf 0.9.58 · forever 1.60.1 (Interface 16001) · 18.11.2026 18:20 UTC** – OK 329 · FEHLER 0 · übersprungen 24 · im Client prüfen 8 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Optionen > Daten & Abgleich: 'Bank-Charakter' auf 'an', Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
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
- [SKIP] CT-C4 L – Spiel: Sperrliste: Bewerbung, Einladen, Tooltip (grund: nur für Offiziere)

**Fehler im Spiel (letzte 7 Tage)**
- 4× `GS_APPS`: Interface/AddOns/GuildSentinel/Roster.lua:124: attempt to index field 'alts' (a nil value) – Version 0.9.51 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 15:47 UTC

## LevelPilot

**Testlauf 3.13.2 · forever 1.60.1 (Interface 16001) · 19.11.2026 11:32 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.13.3 · forever 1.60.1 (Interface 16001) · 19.11.2026 12:07 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.13.4 · forever 1.60.1 (Interface 16001) · 19.11.2026 15:19 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Testlauf 3.13.5 · forever 1.60.1 (Interface 16001) · 20.11.2026 06:31 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Fehler im Spiel (letzte 7 Tage)**
- 15× `Reise`: Fehler in der Reise: Interface/AddOns/LevelPilot/Virtual.lua:135: attempt to perform indexed assignment on field '?' (a boolean value) – Version 3.12.89 · forever 1.60.1 (Interface 16001) · zuletzt 17.11.2026 19:02 UTC

## ProfessionSentinel

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

**Testlauf 0.9.72 · forever 1.60.1 (Interface 16001) · 18.11.2026 12:56 UTC** – OK 1 · FEHLER 1 · übersprungen 8 · im Client prüfen 0
- [FEHLER] S2 S – Fertigkeit und Plan-Start (ergebnis: Fertigkeit 0 | erwartet: > 0)
- [SKIP] S3 S – Zähler sinkt nach einem Skillpunkt (grund: herstellen, bis ein Skillpunkt kommt)
- [SKIP] S4 S – Andocken ohne Überlappen (grund: Rezept wählen, damit das AHSentinel-Gewinn-Fenster erscheint)
- [SKIP] S5 S – Gleiche AH-Gebühr wie AHSentinel (grund: 5 Rezepte im Panel anklicken (Berufsfenster offen))
- [SKIP] S6 S – Rangliste Leveln sortiert (grund: Reiter „Rangliste“ öffnen)
- [SKIP] S7 S – Kein Neuaufbau-Sturm beim Herstellen (grund: 5 Gegenstände hintereinander herstellen)
- [SKIP] S8 S – Oberflächen-Prüfung (Bereich K) (grund: Berufsfenster mit Panel öffnen)
- [SKIP] S9 S – Gekaufte Menge = eingegebene Menge (grund: beim Händler: in der Einkaufsliste eine Menge eingeben und „Kaufen“ klicken)
- [SKIP] S10 S – Shift+Klick öffnet das Mengenfenster (grund: beim Händler: Shift+Klick auf eine Ware, dann noch einmal mit offener Chat-Eingabe)

**Testlauf 0.9.74 · forever 1.60.1 (Interface 16001) · 18.11.2026 18:23 UTC** – OK 1 · FEHLER 1 · übersprungen 8 · im Client prüfen 0
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

**Testlauf 3.0.36 · forever 1.60.1 (Interface 16001) · 18.11.2026 09:07 UTC** – OK 138 · FEHLER 1 · übersprungen 14 · im Client prüfen 10 · Sandbox OK
- [SKIP] T06 A – Fähigkeiten folgen der Weiche (grund: Caps nur beim Laden berechnet)
- [SKIP] T35b B – Berufe: Fenster wird eingelesen (grund: wartet auf Fenster: Berufe – passiert von selbst, wenn du das nächste Mal ein Berufsfenster öffnest)
- [SKIP] T36b B – Bank-Charakter: Bank wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [SKIP] T36c B – Bank-Charakter: Post wird gelesen (grund: kein Bank-Charakter (Einstellungen))
- [FEHLER] T43 B – Test-Werkzeug selbst (ony) (lua: Interface/AddOns/RaidMaster/Test/Test.lua:1062: attempt to call a nil value)
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

**Testlauf 3.0.40 · forever 1.60.1 (Interface 16001) · 18.11.2026 18:21 UTC** – OK 0 · FEHLER 1 · übersprungen 0 · im Client prüfen 0
- [FEHLER] T35b B – Berufe: Fenster wird eingelesen (nachgeholt) (ergebnis: nach dem Öffnen nicht eingelesen | erwartet: Berufe-Daten neu)

## ThreatSentinel

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

**Testlauf 2.5.23 · forever 1.60.1 (Interface 16001) · 18.11.2026 12:49 UTC** – OK 0 · FEHLER 1 · übersprungen 0 · im Client prüfen 0
- [FEHLER] T186 K – Oberfläche mit offenen Blizzard-Fenstern (nachgeholt bei ProfessionsFrame) (ergebnis: Testzentrale überdeckt ProfessionSentinel-Panel (ProfessionSentinel); Einstellungen überdeckt ProfessionSentinel-Panel (ProfessionSentinel) · geprüft 4 | erwartet: keine, geprüft > 0)
