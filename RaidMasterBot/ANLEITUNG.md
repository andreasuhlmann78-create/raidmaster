# RaidMaster-Bot 1.5 – Einrichtung und Bedienung

Der Bot übernimmt Raidanmeldungen (Gilde und PUG mit Soft Reserve), stellt Raids und feste Gruppen
zusammen, postet die DKP-Stände pro Raid, hinterlegt die Skillungen aus dem Spiel und verschickt die
Einteilung als Direktnachricht.

**So arbeiten die drei Teile zusammen:**

| Teil | Wo | Aufgabe |
|---|---|---|
| **Bot** | gemieteter Server (läuft rund um die Uhr) | Discord: Anmeldungen, DKP, Aufstellung, Updates |
| **Uploader** | PC der Raidleitung (wo WoW läuft) | schickt nach jedem `/reload` die Addon-Daten an den Bot |
| **Addon RaidMaster** | bei allen Spielern im Spiel | DKP, Loot, Einteilung, Skillungen |

Updates spielt der Bot selbst ein: Neue Versionen kommen aus eurem GitHub-Repository, der Bot tauscht
seine Dateien aus, startet neu und stellt die neue Addon-ZIP in **#raid-addon** bereit – alle
registrierten Spieler bekommen eine Direktnachricht.

---

## 1. Bot bei Discord anlegen (falls noch nicht geschehen)

1. https://discord.com/developers/applications → **Neue Anwendung** („Raidmaster tool“).
2. Links **Bot** → **Token zurücksetzen** → Token **kopieren** (wie ein Passwort behandeln).
3. Links **OAuth2** → **OAuth2-URL-Generator**: Bereiche **bot** und **applications.commands**,
   Integrationstyp **Gilden-Installation**, Link öffnen und den Bot in euren Server einladen.

Habt ihr den Bot schon auf dem PC benutzt, bleibt alles wie es ist – Token und Server-ID braucht ihr gleich wieder.

## 2. Bot-Rechte im Discord

Servereinstellungen → **Rollen** → **Raidmaster tool** → **Berechtigungen** – einschalten und eingeschaltet lassen:

- **Kanäle verwalten** (eigene Kategorie für neue Raids)
- **Rollen verwalten** (Rolle Gast für PUG-Spieler)
- **Webhooks verwalten** (für den Uploader)
- **Nachrichten verwalten** (verarbeitete Uploads aufräumen)

## 3. Server mieten

Empfehlung: **Infomaniak VPS Lite**, kleinste Stufe (1 vCPU, 2 GB RAM) – ca. CHF 2.90 pro Monat,
12 Monate im Voraus. Jeder andere kleine Linux-Server geht genauso (z. B. netcup VPS nano).

1. Bei der Bestellung als Betriebssystem **Ubuntu 24.04** wählen.
2. Nach der Einrichtung zeigt der Anbieter die **IP-Adresse** und den **Benutzernamen** (meist `ubuntu`)
   bzw. lässt dich einen SSH-Schlüssel hinterlegen.
   SSH-Schlüssel erstellen (falls verlangt): Windows-Taste → **PowerShell** → `ssh-keygen` → dreimal Enter.
   Den Inhalt von `C:\Users\<du>\.ssh\id_ed25519.pub` beim Anbieter einfügen.
3. Verbinden: PowerShell öffnen und eingeben
   `ssh ubuntu@IP-ADRESSE` (beim ersten Mal mit `yes` bestätigen).

## 4. Bot auf dem Server installieren

**Wichtig:** Läuft der Bot noch auf deinem PC, dort zuerst das Fenster schließen – der Bot darf nur
einmal laufen.

Im SSH-Fenster diesen einen Befehl eingeben (BENUTZER/REPO = euer GitHub-Repository, z. B. `goldsentinel/raidmaster`):

```
curl -fsSL https://raw.githubusercontent.com/BENUTZER/REPO/main/RaidMasterBot/install.sh | sudo bash -s BENUTZER/REPO
```

Das Skript installiert alles, fragt nach **Bot-Token** und **Server-ID** und startet den Bot als Dienst.
Er läuft ab jetzt dauerhaft, auch nach einem Neustart des Servers.

Ohne GitHub geht es auch: das RaidMaster-Paket per WinSCP auf den Server kopieren, im Ordner
`RaidMasterBot` `sudo bash install.sh` ausführen.

## 5. Discord einrichten

`/raidmaster-einrichten` ausführen (nur Admins). Der Bot legt an bzw. ergänzt:

- Rollen **Offizier**, **Raidleitung**, **Raider**, **Gast**
- **📌 INFO**: #willkommen, #regeln, #ankündigungen, **#raid-addon** (Downloads)
- **⚔️ RAID-ORGA**: #einteilung
- **Eine Kategorie pro Raid** (🔥 MOLTEN CORE, 🐉 ONYXIAS HORT, 🌲 BARROW DEEPS, 🌋 HYJALGIPFEL) mit
  **-anmeldung**, **-taktik**, **-dkp** und **-loot**
- **🎲 PUG**: #pug-anmeldung, #softreserve, #pug-chat
- **💬 ALLGEMEIN**, **🔊 SPRACHE**, **🔒 OFFIZIERE** (#offiziere, #bot-befehle, **#bot-daten**,
  Sprachkanal nur für Offiziere)

**#bot-daten** sieht nur der Bot (und Admins). Dort landen die Uploads und die tägliche Datensicherung.
In **#bot-befehle** meldet der Bot Updates.

## 6. Uploader auf dem PC der Raidleitung

Der Uploader schickt die Addon-Daten (DKP, Loot, Einteilung, Skillungen) an den Bot. Er braucht nur
Python (ist schon installiert).

1. In Discord `/uploader` ausführen (Admins). Der Bot schickt dir die Datei **uploader_config.json**
   – sie enthält einen geheimen Link, nicht weitergeben.
2. Den Ordner **RaidMasterUploader** aus dem Paket z. B. nach `Dokumente` kopieren und die Datei
   hineinlegen.
3. **`uploader.bat`** doppelklicken. Beim ersten Start sucht er die RaidMaster-Datei von WoW selbst.
   Fenster offen lassen.
4. Automatisch mit Windows starten: `Win + R` → `shell:startup` → Verknüpfung zu `uploader.bat` hineinlegen.

Nach jedem `/reload` oder Ausloggen sind die Daten nach wenigen Sekunden im Discord. Mehrere Offiziere
können den Uploader nutzen – es zählt immer der neueste DKP-Stand.

## 7. Umzug vom PC auf den Server (nur wenn der Bot vorher auf deinem PC lief)

Damit Raids, Charaktere und die DKP-Nachrichten erhalten bleiben:

1. Auf dem PC im Bot-Ordner den Ordner **data** öffnen.
2. `raids.json`, `profiles.json` und `state.json` markieren → Rechtsklick → **Senden an → ZIP-komprimierter Ordner**.
3. In Discord `/daten-import` ausführen und die ZIP anhängen. Der Bot übernimmt die Daten und startet kurz neu.
4. `/raidmaster-einrichten` erneut ausführen (trägt die Kanäle ein und legt #bot-daten an).

## 8. Updates – automatisch

- Alle 30 Minuten prüft der Bot das GitHub-Repository. Gibt es etwas Neues, lädt er es herunter,
  **prüft es**, sichert die aktuelle Version, tauscht die Dateien aus und startet neu.
- Stürzt die neue Version beim Start ab, holt der Bot **automatisch die alte Version zurück** und
  meldet das in #bot-befehle.
- Ist eine neue Addon-Version dabei, postet der Bot sie in **#raid-addon** und schickt allen
  registrierten Spielern eine Direktnachricht.
- `config.json` und alle Daten (Raids, Charaktere, DKP) bleiben bei Updates unangetastet.
- `/update` prüft sofort. `/update datei:<ZIP>` spielt ein Paket von Hand ein (z. B. ohne GitHub).
- `/raidmaster-status` zeigt Version, letzten Upload und Datenstand.

Privates Repository: In `config.json` bei `update_token` einen GitHub-Token mit Leserecht eintragen.

## 9. Neue Raids – automatisch

Betritt das Addon einen **neuen Raid**, legt es einen eigenen DKP-Topf an. Beim nächsten Upload
erkennt der Bot ihn, legt **automatisch eine eigene Kategorie** an und meldet das in #ankündigungen.

## 10. Skillungen

- Jeder Spieler mit RaidMaster ab 1.5.0 schickt seine Skillung automatisch (beim Einloggen und nach
  jeder Änderung). Spieler ohne Addon erfasst das Addon des Raidleiters per **Betrachten**.
- Der Bot übernimmt sie ins Discord-Profil: Anmeldungen und Aufstellung zeigen z. B.
  „Cleo · Priester Schatten“.
- Passt die Rolle nicht zur Skillung (z. B. Schattenpriester als Heiler angemeldet), stellt der Bot
  die Rolle um und schickt dem Spieler eine kurze Nachricht. `/charakter` ändert die Rolle jederzeit
  zurück – eine bewusst gewählte Rolle bleibt, bis sich die Skillung wieder ändert.

---

## Raids und Anmeldungen

**Stammraid (Gilde):** `/raid erstellen` – Titel, Datum, Uhrzeit, **raid** (Molten Core, Onyxia, …),
optional Beschreibung und **max_spieler** (40, 20 oder 10). Der Raid erscheint in der Anmeldung seiner
Kategorie (z. B. #mc-anmeldung).

**PUG-Raid:** `/raid erstellen` mit **modus: PUG-Raid mit Soft Reserve** und **soft_reserve** =
Items pro Spieler (1–3). Er erscheint in #pug-anmeldung, Spieler mit der Rolle **Gast** werden angepingt.

**Für alle:** Knöpfe **Anmelden / Ersatzbank / Vielleicht / Abmelden**, beim ersten Mal Klasse, Rolle
und Charakter festlegen. `/charakter` ändert das Profil.

**PUG-Spieler registrieren sich** einmal über den Knopf in #pug-anmeldung: Rolle Gast + Charakter.

## Soft Reserve (PUG)

- Knopf **Soft Reserve** am Raid oder `/sr raid:<Raid> items:16800, 18823`.
- Die Item-ID steht bei Wowhead in der Adresse (`item=16800`). Ganze Wowhead-Links funktionieren auch.
- Leer abschicken löscht die eigene Reservierung.
- **#softreserve** zeigt pro PUG-Raid eine ständig aktuelle Übersicht.
- Im Spiel geht es auch: Addon-Seite **Soft Reserve** oder `/w <Leiter> !sr 16800`.

## Aufstellung und feste Gruppen

`/raid aufstellung raid:<Raid>` (oder automatisch mit der Erinnerung vor dem Raid) postet die
Aufstellung in **#einteilung** und **#offiziere**:

1. **Optimale Besetzung hat Vorrang:** Zuerst Tanks und Heiler nach Bedarf, dann wichtige Klassen,
   dann Nahkampf und Fernkampf. Die Rolle kommt aus dem Profil – und damit aus der Skillung.
2. **Innerhalb jeder Rolle haben Stammspieler Vorrang** (⭐ = mind. 70 % der letzten 10 Raids).
3. **Gruppe 1 = MT** mit den Tanks, danach Nahkampf-, Fernkampf- und Heilergruppen.
4. Wer nicht hineinpasst, steht auf der **Ersatzbank**.

Der Knopf **„Für RaidMaster“** exportiert Anmeldungen, Soft Reserves, Startzeit und die Gruppen –
im Spiel lädt das Addon dann automatisch ein und sortiert die Gruppen.

## Einteilung als Direktnachricht

Erstellt die Raidleitung im Spiel die **Einteilung** und gibt danach `/reload` ein, postet der Bot die
Übersicht in **#einteilung** und schickt jedem verknüpften Spieler seine Aufgaben als **Direktnachricht**.

## DKP in Discord

- Jeder Raid hat einen eigenen DKP-Topf und einen eigenen Kanal in seiner Kategorie (#mc-dkp usw.).
- `/dkp` zeigt die eigenen DKP in allen Raids, `/dkpliste raid:<Raid>` die Rangliste.
- Neue Items erscheinen im Loot-Kanal des jeweiligen Raids (#mc-loot usw.).
- WoW schreibt die Daten beim **Ausloggen** oder nach **/reload** – der Uploader schickt sie sofort weiter.

## Alle Befehle

| Befehl | Wer | Wofür |
|---|---|---|
| `/raid erstellen` | Offiziere | Raid (DKP oder PUG) zur Anmeldung |
| `/raid aufstellung` | Offiziere | Aufstellung + Gruppen posten |
| `/raid liste`, `schliessen`, `oeffnen`, `absagen`, `export` | Offiziere | Raids verwalten |
| `/raid taktik` | Offiziere | Molten-Core-Taktik in #mc-taktik |
| `/addon` | alle | Download-Link der aktuellen Addon-Version |
| `/sr` | alle | Soft Reserve für PUG-Raids |
| `/charakter` | alle | Charakter und Rolle festlegen |
| `/dkp`, `/dkpliste` | alle | DKP abfragen |
| `/raidmaster-status` | Offiziere | Version, Uploads, Datenstand |
| `/raidmaster-einrichten` | Admins | Server einrichten/ergänzen |
| `/uploader` | Admins | Einrichtung für den Uploader |
| `/update` | Admins | Update prüfen oder ZIP einspielen |
| `/daten-import` | Admins | Daten aus einer Sicherung übernehmen |

## Auf dem Server (SSH)

| Was | Befehl |
|---|---|
| Protokoll live ansehen | `sudo journalctl -u raidmaster -f` |
| Neu starten | `sudo systemctl restart raidmaster` |
| Stoppen / starten | `sudo systemctl stop raidmaster` / `sudo systemctl start raidmaster` |
| Einstellungen ändern | `sudo nano /opt/raidmaster/config.json` (danach neu starten) |

## Probleme?

- **„Die Anwendung reagiert nicht“:** `/raidmaster-status` bzw. auf dem Server das Protokoll ansehen.
  Läuft der Bot noch zusätzlich auf deinem PC? Dann dort beenden.
- **Keine Daten aus dem Spiel:** Läuft `uploader.bat`? Im Fenster muss nach `/reload` „Hochgeladen“
  stehen. `/raidmaster-status` zeigt den letzten Upload. Zeigt der Bot-Protokoll „Upload ohne Anhang“,
  im Entwicklerportal unter **Bot → Privileged Gateway Intents** den **Message Content Intent** einschalten,
  in `config.json` `"message_content_intent": true` setzen und den Bot neu starten.
- **Keine Direktnachricht:** Charakter nicht verknüpft (`/charakter`) oder Direktnachrichten in den
  Discord-Privatsphäre-Einstellungen gesperrt.
- **Sicherungen:** täglich in #bot-daten und auf dem Server unter `/opt/raidmaster/backup`.

## Ohne Server (Bot auf dem eigenen PC)

Geht weiterhin: `start.bat` doppelklicken und in `config.json` bei `savedvariables_path` den Pfad zur
`RaidMaster.lua` eintragen (`WTF/Account/<KONTO>/SavedVariables/RaidMaster.lua`, mit `/`).
Der Bot läuft dann nur, solange der PC an ist; den Uploader braucht es so nicht.
