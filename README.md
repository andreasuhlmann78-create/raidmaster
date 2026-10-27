# RaidMaster

Raid-Werkzeuge für die Gilde auf **WoW Forever**.

## Download Addon

**Aktuelle Version: [RaidMaster-3.0.4.zip](https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/RaidMaster-3.0.4.zip)**
(immer die neueste: [RaidMaster-latest.zip](https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/RaidMaster-latest.zip))

**Test-Werkzeug für die Raidleitung:** in RaidMaster eingebaut (ab 2.1.0) – Knopf „Test“ oben im RaidMaster-Fenster oder `/rmtest`. Den alten Ordner `RaidMasterTest` bitte löschen.

**Uploader für den PC der Raidleitung (DKP automatisch in Discord):** [RaidMasterUploader.zip](https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/RaidMasterUploader.zip) – Anleitung im Spiel: Seite *Discord* oder `/rm discord`

**AH Analyzer Pro:** [AHAnalyzerPro-0.60.1.zip](https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/AHAnalyzerPro-0.60.1.zip)

**BuffSentinel** (Buff-Erinnerungen, Proc-Buttons und Cooldowns mit Ein-Klick-Buttons, alle WoW-Versionen): [BuffSentinel-0.5.0.zip](https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/BuffSentinel-0.5.0.zip)

ZIP entpacken und den Ordner `RaidMaster` nach `Interface/AddOns` kopieren (alten Ordner ersetzen).
Läuft in allen WoW-Versionen (Classic Era, WoW Forever, TBC, Wrath, Cata, MoP Classic, Retail) und in 11 Sprachen – mit allen Raids von Classic bis Midnight (Taktiken, Raidchat-Infos, Markierungsvorlagen).

| Ordner | Inhalt |
|---|---|
| `RaidMaster/` | WoW-Addon: DKP pro Raid, Versteigerung, Loot, PUG mit Soft Reserve, Einteilung, Auto-Einladung, Skillungen |
| `RaidMasterBot/` | Discord-Bot: Anmeldungen, Aufstellung, DKP-Kanäle, Direktnachrichten, Selbst-Update |
| `RaidMasterUploader/` | Uploader für den PC der Raidleitung: schickt die Addon-Daten an den Bot |

Installation und Bedienung: [RaidMasterBot/ANLEITUNG.md](RaidMasterBot/ANLEITUNG.md) und
[RaidMaster/LIESMICH.txt](RaidMaster/LIESMICH.txt).

Server-Installation (Ubuntu/Debian):

```
curl -fsSL https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/main/RaidMasterBot/install.sh | sudo bash -s andreasuhlmann78-create/raidmaster
```

Der Bot prüft dieses Repository alle 30 Minuten und installiert neue Versionen selbst.
Neue Addon-Versionen veröffentlicht er in #raid-addon.

## Lizenz

© GoldSentinel – Alle Rechte vorbehalten / All rights reserved. Benutzen erlaubt; verändern, weitergeben oder
veröffentlichen nur mit schriftlicher Erlaubnis. Siehe [LICENSE.txt](LICENSE.txt).
