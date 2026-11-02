# GoldSentinelGame.lua – gemeinsame Versionserkennung für alle GoldSentinel-Addons

Für Claude in den Projekten RaidMaster, AHSentinel, GuildSentinel, ThreatSentinel, BuffSentinel und LevelPilot.
Grundlage: übergreifender Auftrag vom 02.11.2026, Punkt 1. Eingebaut zuerst in ProfessionSentinel 0.9.3.

## Warum

Jedes Addon erkannte WoW Forever bisher anders, und mehrere zählten es fälschlich zu Classic:

| Addon | Bisherige Erkennung |
|---|---|
| RaidMaster | `RM.IsClassicEra = … or RM.GAME.key == "forever"` |
| BuffSentinel | `isRetail` |
| ThreatSentinel | `isRetail` ab 110000 |

Das ist die Ursache der meisten Fehler. Forever **sieht** aus wie Classic, läuft aber auf dem **modernen** Client: C_TradeSkillUI, C_Container, Retail-Berufsfenster, Secret Values. Forever ist deshalb **nie** „Classic“.

## Die Datei

- Referenzkopie: `shared/GoldSentinelGame.lua` im Raidmaster-Repo, Test: `shared/test_gamelib.py`.
- Sie funktioniert wie GoldSentinelDev.lua: Jedes Addon bringt eine Kopie mit, die neueste Version (`VERSION`) gewinnt.
- **Ändern nur an der Referenzkopie:** `VERSION` erhöhen, Test laufen lassen, dann in alle Addons kopieren.

| Feld | Bedeutung |
|---|---|
| `GoldSentinelGame.flavor` | `"era"`, `"forever"`, `"tbc"`, `"wrath"`, `"cata"`, `"mists"`, `"retail"` oder `nil` |
| `.IsForever` | Interface 16000–19999 oder `WOW_PROJECT_CAMELOT` |
| `.IsEra` | Interface 11400–11599 |
| `.IsRetail` | Interface ab 100000 oder `WOW_PROJECT_MAINLINE` |
| `.IsClassic` | Era, TBC, Wrath, Cata, MoP Classic, **nicht** Forever |
| `.IsModern` | Forever oder Retail, also moderne API |
| `.HasSecrets` | Das Spiel kennt `issecretvalue` |
| `.IsSecret(v)` | true bei Secret Value, nie ein Fehler, false ohne `issecretvalue` |
| `.Safe(v)` | `v` oder `nil`, wenn `v` ein Secret Value ist |
| `.interface`, `.gameVersion`, `.build` | z. B. 16001, „1.60.1“, „70707“ |
| `:Status()`, `/gsgame` | Diagnose-Text im Chat |

## Einbau, Addon für Addon

1. `GoldSentinelGame.lua` ins Addon kopieren.
2. In **jeder** .toc des Addons direkt nach `GoldSentinelDev.lua` eintragen, vor allen eigenen Dateien.
3. Die eigene Erkennung darauf umstellen. Die eigenen Namen dürfen bleiben, damit der übrige Code nicht angefasst werden muss, z. B. für RaidMaster:
   ```lua
   local G = GoldSentinelGame
   RM.IsForever    = G.IsForever
   RM.IsClassicEra = G.IsEra          -- NICHT mehr Forever
   RM.IsModern     = G.IsModern       -- moderne API: Forever und Retail
   ```
4. **Danach jede Stelle prüfen, die die alte Erkennung benutzt hat.** Wo Code für „Classic“ wegen Forever lief, gehört er jetzt zu `IsModern`.
   - Am sichersten ist es, nach der Funktion zu fragen: `if C_TradeSkillUI and C_TradeSkillUI.X then … else … end`.
   - Ereignisse nur mit `pcall(frame.RegisterEvent, frame, "EVENT")` anmelden. Unbekannte Ereignisse lösen sonst einen Lua-Fehler aus.
5. Werte, die im Kampf Secret Values sein können (Gesundheit, Bedrohung, Namen in Retail und Forever), vor Vergleichen und Rechnungen durch `GoldSentinelGame.Safe(v)` schicken.
6. Testen:
   - `python3 -I shared/test_gamelib.py` (die Datei selbst)
   - die eigenen Tests des Addons
   - im Spiel `/gsgame` (zeigt die erkannte Version)
7. Wie immer: komplette Dateien liefern, alte Versionen nie brechen, Version erhöhen, Changelog auf Deutsch und Englisch.

## Vorbild

So nutzt ProfessionSentinel 0.9.3 die Datei: `Flavor.lua` im Repo andreasuhlmann78-create/ProfessionSentinel. Es übernimmt `GoldSentinelGame.flavor` und erlaubt davon nur Forever, Era und Retail. Der Selbsttest prüft, dass beide Erkennungen übereinstimmen.

## Noch nicht drin (folgt, sobald im Client bestätigt)

Punkt 4 des Auftrags: Vor- und Nachnamen in Forever. Ein gemeinsamer Namensvergleich kommt als Version 2 in diese Datei, erst wenn im Forever-Client bestätigt ist, wie Namen aussehen.
