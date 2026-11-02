# Discord-Prüfung – steht im Discord, was im Repo liegt?

Für den Nutzer und für Claude in **allen** Projekten (ProfessionSentinel, AHSentinel, GuildSentinel, ThreatSentinel, BuffSentinel, LevelPilot, RaidMaster …).

## Was geprüft wird

Ein GitHub-Workflow liest mit dem Konto des RaidMaster-Bots die Discord-Kanäle. Er liest nur, er schreibt nichts in Discord. Dann vergleicht er:

1. **Ankündigungen** (`announce/<kanal>__<name>-<version>.md`)
   - Pro Reihe zählt nur die neueste Fassung.
   - Geprüft wird, ob jede Zeile der Datei im Kanal steht, gepostet oder bearbeitet vom Bot.
   - Fehlende Zeilen werden aufgelistet. So sieht man auch, ob eine Beschreibung wirklich angepasst wurde.
2. **Addon-Veröffentlichungen aus `download/`**, die der Bot selbst postet (zurzeit AHSentinel in #aktionshaus)
   - Geprüft wird, ob es den Beitrag „**AHSentinel 0.64.2** ist da“ mit der ZIP gibt.

Den Upload auf CurseForge sieht man in `curseforge/uploaded.json`.

## Wann der Workflow läuft

- Nach jedem Push in `announce/` oder `download/`. Er wartet zuerst 35 Minuten, weil der Bot Änderungen etwa alle 30 Minuten abholt.
- Zweimal am Tag automatisch.
- Jederzeit von Hand (siehe unten).

## Ergebnis

Das Ergebnis liegt im Repo **andreasuhlmann78-create/raidmaster** (öffentlich):

- `discord-check/status.md`: Tabelle zum Lesen
- `discord-check/status.json`: maschinenlesbar, mit `ok`, `wartet` und den Einträgen

Bedeutung des Status:

| Status | Bedeutung |
|---|---|
| ✅ ok | steht vollständig im Discord |
| ⏳ wartet | Push ist jünger als 45 Minuten. Der Bot hat noch nicht abgeholt, das ist normal. |
| ⚠️ veraltet | Beitrag da, aber einzelne Zeilen fehlen: alte Fassung oder Bearbeitung nicht übernommen |
| ❌ fehlt | Kanal da, Beitrag nicht |
| ❌ kanal_fehlt | Kanal mit diesem Namen gibt es nicht |
| 🔒 kein_zugriff | Bot darf den Kanal nicht lesen |

## Für Claude: so prüfst du

**Nur nachsehen** (letztes Ergebnis):

```bash
gh api repos/andreasuhlmann78-create/raidmaster/contents/discord-check/status.md -H "Accept: application/vnd.github.raw"
```

Ohne `gh`:

```
WebFetch https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/main/discord-check/status.md
```

**Neu prüfen lassen** (dauert etwa 1 Minute):

Nur REST-Aufrufe verwenden. `gh workflow run` und `gh run watch` brauchen GraphQL, und das ist in Claude-Sitzungen gesperrt.

```bash
R=andreasuhlmann78-create/raidmaster
gh api -X POST repos/$R/actions/workflows/discord-check.yml/dispatches -f ref=main -f "inputs[warten]=0"
# Lauf-ID holen (ein paar Sekunden nach dem Start)
RUN=$(gh api "repos/$R/actions/workflows/discord-check.yml/runs?per_page=1" --jq '.workflow_runs[0].id')
# Status abfragen, bis "completed" kommt (etwa 30-60 s)
gh api repos/$R/actions/runs/$RUN --jq '.status+" "+(.conclusion//"")'
# Ergebnis lesen
gh api repos/$R/contents/discord-check/status.md -H "Accept: application/vnd.github.raw"
```

Gerade erst gepusht? Dann `-f warten=35`, oder einfach den automatischen Lauf nach dem Push abwarten und später nachsehen.

**Danach dem Nutzer sagen**, was der Status zeigt:

- Alles ✅: kurz bestätigen.
- ⏳ wartet: sagen, dass der Bot noch abholt, mit ungefährer Uhrzeit.
- ⚠️ oder ❌ älter als 45 Minuten: das Problem nennen (z. B. Kanal fehlt, Zeile fehlt) und eine Lösung vorschlagen.

## Für den Nutzer: einmal einrichten

Der Workflow braucht den Bot-Token als **GitHub-Secret**. Der Token gehört nie in eine Datei oder in den Chat.

1. Auf GitHub das Repo **raidmaster** öffnen.
2. Zu **Settings → Secrets and variables → Actions → New repository secret** gehen.
3. Als Name `DISCORD_BOT_TOKEN` eintragen, als Wert denselben Token wie in der `config.json` des Bots (Feld `token`). Speichern.
4. Optional, falls der Bot auf mehreren Servern ist: Unter **Variables** `DISCORD_GUILD_ID` mit der Server-ID anlegen.
5. Testen: **Actions → Discord-Prüfung → Run workflow**.

## Absichtlich gelöschte Ankündigungen

Steht eine Ankündigung absichtlich nicht mehr im Discord, z. B. eine abgeschlossene Abstimmung, trägst du den Dateinamen in `discord-check/ignorieren.txt` ein.
