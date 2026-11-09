# Hinweise für Claude-Sitzungen in diesem Repo

Dieses Repo gehört GoldSentinel. Hier veröffentlichen alle GoldSentinel-Addons (`download/`, `announce/`), und hier liegen
das Prüfsystem (`addon-check/`, `shared/`, `testberichte/`) und der Discord-Bot (`RaidMasterBot/`).

## Aufträge der Prüf-Sitzung – vor jeder Arbeit an einem Addon lesen

Ausnahme: Geplante Aufgaben (z. B. «ProfessionSentinel Rezeptdaten-Update», «Raids und Taktiken für WoW Forever») führen nur
ihre eigene Anweisung aus. Sie setzen keine Aufträge aus `auftraege/` um und ändern keinen Programmcode.

Die Prüf-Sitzung verteilt Anweisungen, Korrekturen und Hinweise für die Addon-Projekte über den Ordner `auftraege/`
(Regeln in `auftraege/README.md`). Ein Ordner pro Addon: `RaidMaster/`, `ThreatSentinel/`, `AHSentinel/`, `BuffSentinel/`,
`GuildSentinel/`, `ProfessionSentinel/`, `LevelPilot/`.

1. `git pull --rebase`
2. Alle Dateien in `auftraege/<dein Addon>/` lesen. Neues zeigt `git log --oneline -- auftraege/<dein Addon>/`.
   `offen-<addon>.txt` ist immer vollständig, mit allem, was noch offen ist.
3. Umsetzen: komplette Dateien, alte Clients nie brechen, Locales und CHANGELOG EN/DE.
4. Vor dem Push: `python3 addon-check/addon_check.py download/<Addon>-<Version>.zip` -> kein FEHLER.
5. Dem Nutzer melden, was umgesetzt wurde. Ist ein Befund falsch, begründet zurückmelden.

Den Ordner `auftraege/` ändert nur die Prüf-Sitzung. Gemeinsame Dateien (`GoldSentinelGame.lua`, `GoldSentinelTest.lua`,
`GoldSentinelDev.lua`) nur unverändert aus `shared/` kopieren, nie selbst ändern.

## Nur eine Sitzung je Addon (Entscheid des Nutzers, 9. November 2026)

Am 9.11. haben zwei Sitzungen gleichzeitig AHSentinel geändert und veröffentlicht (0.65.18 bis 0.65.20). Das darf
nicht wieder passieren, sonst überschreiben sie sich gegenseitig.

- **AHSentinel ändert und veröffentlicht nur noch EINE Sitzung:** die AHSentinel-Sitzung des Nutzers.
  Alle anderen Sitzungen, die Prüf-Sitzung und geplante Aufgaben ändern AHSentinel nicht und veröffentlichen nichts
  davon (Repo AHAnalyzerPro, `download/AHSentinel-*`, `announce/ahsentinel__*`). Sie melden Befunde nur über
  `auftraege/AHSentinel/` bzw. dem Nutzer.
- Gilt sinngemäss für jedes Addon: je Addon arbeitet nur seine eigene Sitzung daran.
- Vor jeder Veröffentlichung trotzdem `git pull --rebase` und die höchste schon veröffentlichte Version prüfen.

## Neues Addon

Neue GoldSentinel-Addons immer aus der Vorlage erstellen: `python3 shared/vorlage/neues_addon.py <Name> --slash <befehl>
--en "…" --de "…" --zip` (Anleitung in `shared/vorlage/README.md`). Die Vorlage hält alle Regeln der Prüfung schon ein.

## Wirtschaft, Preise, Gebühren (Pflicht)

Wer Preise, Gebühren, Gewinne oder Werte berechnet, prüft oder beauftragt, liest vorher
`shared/wissen/wirtschaft-forever.md` und hält dessen Abschnitt 0 (zuerst messen, Zahlen müssen exakt aufgehen) und die
Pflicht-Checkliste (Abschnitt 7) ein. Regeln nur als "belegt" weitergeben, sonst als Messauftrag.

## Addon-Kommunikation (Pflicht)

Wer Sync, Addon-Nachrichten oder Kanäle baut oder beauftragt, liest vorher `shared/wissen/kommunikation-forever.md`.
In WoW Forever kommen Addon-Nachrichten über eigene Chat-Kanäle nicht an.

## Immer

- Das Repo ist öffentlich: nie Tokens, Webhook-URLs, Passwörter oder Spielernamen in Dateien oder Commits.
  `config.json` und `uploader_config.json` nie anfassen.
- Andere Addons als das eigene nicht ändern.
