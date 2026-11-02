# Automatischer CurseForge-Upload

Sobald eine neue Addon-Zip in `download/` landet, lädt GitHub sie selbst auf CurseForge hoch
(Workflow `.github/workflows/curseforge.yml`, Skript `upload.py`).

| Datei | Zweck |
|---|---|
| `projects.json` | Projekt-ID pro Addon, Release-Typ, auszulassende Spielversionen (z. B. `"12.1.5"`) |
| `uploaded.json` | bereits hochgeladene Versionen (pflegt der Workflow selbst) |
| `AHSentinel-description.md` / `.html` | englische Projektbeschreibung zum Einfügen auf CurseForge |
| `make_description.py` | schreibt den Abschnitt „What's new“ der Beschreibung neu (letzte 5 Versionen aus `CHANGELOG.md`) |

Einmalig nötig:
1. API-Token: https://authors.curseforge.com/#/settings/api-tokens
2. Token als GitHub-Secret `CF_API_KEY` speichern (Settings → Secrets and variables → Actions).
3. Projekt-ID in `projects.json` eintragen.

Version und Spielversionen kommen aus der `.toc` in der Zip, der Changelog aus dem passenden
Abschnitt in `CHANGELOG.md`. WoW Forever (16001) kennt CurseForge nicht, es wird ausgelassen.
Manuell starten: GitHub → Actions → CurseForge-Upload → Run workflow.

Beschreibung: CurseForge hat keine Schnittstelle, um die Projektbeschreibung zu ändern.
Nach jedem Upload erzeugt der Workflow deshalb `AHSentinel-description.html` mit den
Neuerungen der letzten 5 Versionen neu – diese Datei auf CurseForge unter
„Description“ einfügen (Quelltext-Ansicht). Von Hand: `python3 curseforge/make_description.py`.
