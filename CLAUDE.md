# Hinweise für Claude-Sitzungen in diesem Repo

Dieses Repo gehört GoldSentinel. Hier veröffentlichen alle GoldSentinel-Addons (`download/`, `announce/`), und hier liegen
das Prüfsystem (`addon-check/`, `shared/`, `testberichte/`) und der Discord-Bot (`RaidMasterBot/`).

## Aufträge der Prüf-Sitzung – vor jeder Arbeit an einem Addon lesen

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

## Immer

- Das Repo ist öffentlich: nie Tokens, Webhook-URLs, Passwörter oder Spielernamen in Dateien oder Commits.
  `config.json` und `uploader_config.json` nie anfassen.
- Andere Addons als das eigene nicht ändern.
