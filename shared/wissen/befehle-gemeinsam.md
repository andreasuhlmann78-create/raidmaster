# Gemeinsame Befehle aller GoldSentinel-Addons (CH-G)

> VORSCHLAG der AHSentinel-Sitzung (FREIGABE PHASE 8 Punkt 4, Nutzer 16.11.2026 14:10) – wartet auf die Prüfung durch den
> Supervisor. Muster ist `/ahs hilfe` (AHSentinel, ab 0.65.270). Andere Addons ändern NUR ihre eigenen Sitzungen.

## Ziel

Wer ein GoldSentinel-Addon kennt, kennt alle: dieselben Wörter tun in jedem Addon dasselbe, die Hilfe sieht überall gleich
aus, deutsch und englisch gehen immer (unabhängig von der Spielsprache). Die Befehlsliste beim Tippen
(`shared/GoldSentinelCmdHint.lua`) zeigt sie dann ohne Zusatzarbeit.

## 1. Aufbau von `/<kürzel> hilfe`

```
<Addon> – Befehle  (auch /<langer Name>)
 Alltag
   /<kürzel>              -  Fenster öffnen / schließen
   /<kürzel> <wort>       -  … (die Befehle des Addons, wichtigste zuerst)
 Einstellungen
   /<kürzel> optionen     -  Optionen
   /<kürzel> sprache      -  Sprache des Addons wechseln
   /<kürzel> minikarte    -  Knopf an der Minikarte an / aus
   /<kürzel> reset        -  Fenster- und Knopf-Positionen zurücksetzen
 Hilfe
   /<kürzel> handbuch     -  Anleitung (Fenster)
   /<kürzel> debug        -  Diagnose im Chat (für Fehlermeldungen)
   /<kürzel> spenden      -  Addon unterstützen
   /<kürzel> hilfe        -  Diese Liste
 Entwickler (nur im Entwicklermodus sichtbar)
   /<kürzel> prüfliste    -  Prüfliste im Spiel
   /<kürzel> testroutine  -  Testroutine (Bericht an die Prüfung)
   /<kürzel> test         -  Selbsttest
   /<kürzel> protokoll    -  Diagnose-Protokoll
```

- Vier Gruppen in dieser Reihenfolge: **Alltag, Einstellungen, Hilfe, Entwickler**. Eine Zeile je Befehl:
  `   /<kürzel> <wort>  -  <Beschreibung>`; Gruppen-Überschrift gelb, Befehl grün (wie bisher).
- Das Wort wird in der Sprache des Addons gezeigt (deutsch oder englisch), angenommen werden immer beide.
- Entwickler-Befehle erscheinen nur im Entwicklermodus (`/<kürzel> entwickler an`, GoldSentinelDev).
- Gibt es einen Standard-Befehl im Addon nicht (z. B. kein Minikarten-Knopf), fehlt die Zeile – das Wort wird für nichts
  anderes benutzt.

## 2. Standard-Wörter (gleiche Bedeutung in jedem Addon)

| Deutsch (gezeigt) | Englisch (gezeigt) | auch angenommen | Bedeutung |
|---|---|---|---|
| (leer) | (leer) | – | Hauptfenster öffnen / schließen |
| hilfe | help | ?, befehle, commands | diese Liste |
| optionen | options | einstellungen, config, settings | Optionen-Fenster |
| sprache | language | lang | Sprache des Addons wechseln |
| minikarte | minimap | – | Minikarten-Knopf an / aus |
| reset | reset | – | Fenster-/Knopf-Positionen zurücksetzen |
| handbuch | manual | anleitung | Anleitung im Fenster |
| debug | debug | – | Diagnose im Chat |
| spenden | donate | support | Addon unterstützen |
| prüfliste | checklist | pruefliste | Prüfliste im Spiel (Entwickler) |
| testroutine | testroutine | – | Testroutine, Bericht an die Prüfung (Entwickler) |
| test | test | selbsttest, selftest | Selbsttest (Entwickler) |
| protokoll | log | diag, diagnose | Diagnose-Protokoll zum Kopieren (Entwickler) |
| entwickler an / aus | developer on / off | – | Entwicklermodus (versteckt, nicht in der Liste) |

Regeln:
1. Diese Wörter bedeuten in keinem Addon etwas anderes (z. B. „test“ ist nie ein Spiel-Befehl).
2. Umlaut-freie Form immer mit annehmen (`pruefliste`, `zurueck`).
3. Ein Addon darf zusätzlich eigene Namen behalten, die es schon lange hat (LevelPilot „zentrale“ = optionen) – dann
   nimmt es das Standard-Wort ZUSÄTZLICH an und zeigt in der Hilfe das Standard-Wort.
4. Die Befehlsliste beim Tippen bekommt dieselbe Tabelle (`commands` an `GoldSentinelCmdHint.Register`), Spalte `w`
   enthält alle angenommenen Formen, `dev = true` für Entwickler-Befehle; neu: `grp` = "alltag" / "einstellungen" /
   "hilfe" / "entwickler" (für die Gruppen in `/… hilfe`).

## 3. Ist-Stand (Code-Suche der AHSentinel-Sitzung, 16.11.2026 – Verdacht, von den Sitzungen zu bestätigen)

| Addon | Kürzel | hilfe | optionen | prüfliste | testroutine | protokoll | sprache | minikarte | spenden |
|---|---|---|---|---|---|---|---|---|---|
| AHSentinel | /ahs | ja | ja | ja | ja | ja | ja | ja | ja |
| BuffSentinel | /bsen | ja | ja (auch config) | ja | ja | ja | ? | ? | ja |
| GuildSentinel | /gs | ja | ? (einstellungen) | ja | ja | ja | ja | ? | ja |
| LevelPilot | /lp | ja | „zentrale“ | ja | ja | ja | ja | ja | ja |
| ProfessionSentinel | /ps | ja | ja | ? | ja | ja | ja | ja | ? |
| ThreatSentinel | /ts | ? | ja (auch config) | ? | ja | ja | ja | ? | ja |
| RaidMaster | /rm | ? | ja | ja | ja | ja | ja | ja | ja |

„?“ = in der Code-Suche nicht eindeutig gefunden; die jeweilige Sitzung prüft selbst.

## 4. Reihenfolge

1. AHSentinel zuerst (Muster, 0.65.270): Gruppen in `/ahs hilfe`, Standard-Wörter mit allen Formen.
2. Der Supervisor prüft und gibt den Text frei; danach je Addon ein Auftrag an die eigene Sitzung.
