# RaidMaster-Bot 1.5 – Einrichtung und Bedienung

Der Bot übernimmt Raidanmeldungen (Gilde und PUG), stellt Raids und feste Gruppen
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
- **Server verwalten** (erkennen, wer über den PUG-Einladungslink beitritt)
- **Events verwalten** (jeder Raid erscheint als Discord-Ereignis im Kalender des Servers)

Außerdem im Entwicklerportal unter **Bot → Privileged Gateway Intents** den **Server Members Intent**
einschalten (damit der Bot neue Mitglieder sieht).

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
- **📌 INFO**: #willkommen, #regeln, #ankündigungen
- **⚔️ RAID-ORGA**: #einteilung
- **🧩 RAID-ADDON** (direkt darunter): **#raid-addon** (Downloads, automatisch vom Bot) und #addon-hilfe
- **Addon's by GoldSentinel** (direkt darunter, **nur für Offiziere**): #aktionshaus – neue Versionen von
  **AH Analyzer Pro** postet der Bot dort automatisch (per `/addon-hochladen` oder über GitHub)
- **Eine Kategorie pro Raid** (🔥 MOLTEN CORE, 🐉 ONYXIAS HORT, 🌲 BARROW DEEPS, 🌋 HYJALGIPFEL) mit
  **-anmeldung** (mit Knopf **Charakter registrieren**), einem **Sprachkanal** (z. B. 🔊 Molten Core),
  **-taktik**, **-dkp** und **-loot**
- **🎲 PUG**: #pug-anmeldung, #pug-chat, Sprachkanal PUG-Raid
- **💬 ALLGEMEIN**, **🔊 SPRACHE**, **🔒 OFFIZIERE** (#offiziere, **#befehlsliste**, #bot-befehle,
  **#bot-daten**, Sprachkanal nur für Offiziere)

**#befehlsliste** zeigt alle Bot-Befehle und hält sich bei jedem Update selbst aktuell. Dort schreibt nur
der Bot – Offiziere können lesen, aber nichts posten.

Die Rolle **Gast** sieht nur **INFO**, **RAID-ADDON** und **PUG** (mit Sprachkanal „PUG-Raid“). Gildenmitglieder
sind davon nicht betroffen.

**#bot-daten** sieht nur der Bot (und Admins). Dort landen die Uploads und die tägliche Datensicherung.
In **#bot-befehle** meldet der Bot Updates.

## 6. PUG-Spieler einladen

`/pug-einladung` (Offiziere) erstellt einen eigenen Einladungslink. Wer darüber beitritt, bekommt
automatisch die Rolle **Gast**, sieht nur INFO und PUG und erhält eine Begrüßung mit Anleitung.
Über eure normalen Einladungslinks kommt man wie bisher auf den ganzen Server.

Werbung im Spiel: Addon-Seite **Werbung** – postet einen Text mit dem Link in den Welt-/Handelskanal.
Der Link kommt beim Import eines PUG-Raids automatisch ins Addon.

## 7. Uploader auf dem PC der Raidleitung

Der Uploader schickt die Addon-Daten (DKP, Loot, Einteilung, Skillungen) an den Bot. Er braucht nur
Python (ist schon installiert).

1. In Discord `/uploader` ausführen (Admins). Der Bot schickt dir per **Direktnachricht** das Programm
   **RaidMasterUploader.zip** und die Datei **uploader_config.json** – sie enthält einen geheimen Link, nicht weitergeben.
   Nur ein Update des Programms (ohne neue Einrichtungsdatei): `/uploader nur_programm:True`.
2. **RaidMasterUploader.zip** z. B. nach `Dokumente` entpacken und **uploader_config.json** in den Ordner legen.
3. **`uploader.bat`** doppelklicken. Beim ersten Start sucht er die RaidMaster-Datei von WoW selbst.
   Fenster offen lassen.
4. Automatisch mit Windows starten: `Win + R` → `shell:startup` → Verknüpfung zu `uploader.bat` hineinlegen.

Nach jedem `/reload` oder Ausloggen sind die Daten nach wenigen Sekunden im Discord. Mehrere Offiziere
können den Uploader nutzen – es zählt immer der neueste DKP-Stand.

## 8. Umzug vom PC auf den Server (nur wenn der Bot vorher auf deinem PC lief)

Damit Raids, Charaktere und die DKP-Nachrichten erhalten bleiben:

1. Auf dem PC im Bot-Ordner den Ordner **data** öffnen.
2. `raids.json`, `profiles.json` und `state.json` markieren → Rechtsklick → **Senden an → ZIP-komprimierter Ordner**.
3. In Discord `/daten-import` ausführen und die ZIP anhängen. Der Bot übernimmt die Daten und startet kurz neu.
4. `/raidmaster-einrichten` erneut ausführen (trägt die Kanäle ein und legt #bot-daten an).

## 9. Updates – automatisch

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

## 10. Neue Raids – automatisch

Betritt das Addon einen **neuen Raid**, legt es einen eigenen DKP-Topf an. Beim nächsten Upload
erkennt der Bot ihn, legt **automatisch eine eigene Kategorie** an und meldet das in #ankündigungen.

## 11. Skillungen

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

**PUG-Raid:** `/raid erstellen` mit **modus: PUG-Raid (softres.it)** und optional **softres** = Link zum
softres.it-Raid (oder später mit `/raid softres`). Er erscheint in #pug-anmeldung mit dem softres.it-Link,
Spieler mit der Rolle **Gast** werden angepingt. Kein DKP – Soft Reserve und Loot laufen über softres.it.
Der Link kommt mit „Für RaidMaster“ ins Addon (Ansage im Raid und Werbetext).

**Für alle:** Knöpfe **Anmelden / Ersatzbank / Vielleicht / Abmelden**, beim ersten Mal Klasse, Rolle
und Charakter festlegen. `/charakter` ändert das Profil.

**Gildenspieler registrieren sich** einmal über den Knopf **Charakter registrieren** in der Anmeldung
ihres Raids (z. B. #mc-anmeldung). **PUG-Spieler** nehmen den Knopf in #pug-anmeldung: Rolle Gast + Charakter.

- **Testraid:** `/raid testraid` (Offiziere/Raidleitung) legt einen Raid „TEST Molten Core“ mit 40 Anmeldungen
  (zufällige Namen, MC-Aufstellung), 5 auf der Ersatzbank und 3 „Vielleicht“ an – zum Ausprobieren von Anmeldung,
  „Für RaidMaster“-Export und Einteilung. Optional `raid:` und `fraktion:` (Paladine oder Schamanen).
  Nach 2 Stunden verschwindet er samt Nachricht von selbst.

## Ruhmeshalle, Ereignisse, Ersatz, Gildenbank

- **#ruhmeshalle** legt der Bot selbst an (nur der Bot schreibt). Dort erscheinen:
  - **Erstkills** mit Screenshot (macht RaidMaster beim Erstkill, schickt der Uploader ab 1.6.0 mit), Datum,
    Versuchen, Kampfdauer und allen Teilnehmern.
  - **Neue Rekorde**: schneller als die bisherige Bestzeit. Alle Bestzeiten: `/rekorde`.
  - **Erfolge**: Unermüdlich (10 Raids am Stück), Stammgast (25 Raids), Urgestein (50), Bossjäger (100 Bosse),
    Retter in der Not (5× von der Ersatzbank), Glückspilz (10 Items), „Erster <Boss>“. Abfragen: `/erfolge [Name]`.
  - **Raider des Monats** am Monatsanfang (Raid dabei 10 Punkte, pünktlich 2, Ersatzbank bereit 5) – bekommt
    für einen Monat die Rolle **⭐ Raider des Monats**. Rangliste: `/raider-des-monats`.
- **Discord-Ereignisse:** Jeder neue Raid erscheint als Ereignis (Kalender oben im Server, Erinnerung von Discord).
  Für ältere Raids: `/raid-ereignisse`. Beim Absagen wird das Ereignis gelöscht. Ausschalten: `"raid_events": false`.
- **Ersatz bei Absage:** Meldet sich jemand in den letzten 48 Stunden vor dem Raid ab, fragt der Bot den
  passendsten Spieler der Ersatzbank (gleiche Rolle, dann gleiche Klasse) per Direktnachricht mit Knopf
  „Ich komme!“. Ausschalten: `"auto_substitute": false`.
- **Gildenbank:** Auf dem Bank-Charakter in RaidMaster → Einstellungen „Bank-Charakter“ anhaken. Öffnet er Bank
  oder Briefkasten, liest das Addon den Bestand. Der Uploader auf seinem PC schickt ihn mit, der Bot zeigt ihn in
  **#gildenbank** (eine Nachricht, wird aktualisiert) und mit `/bank Feuerschutz`.

## Twinks, Berufe, DKP-Nachricht, Verfall

- **Twinks:** `/twink hinzufügen` (Name, Klasse, Rolle), `/twink wechseln` (mit welchem Charakter du dich anmeldest),
  `/twink liste`, `/twink entfernen`. In der Anmeldung steht „Twink von …“; in der Aufstellung kommen Mains vor Twinks.
  Der Export „Für RaidMaster“ enthält die Twinks – im Addon gilt dann „Main vor Twink“ beim Bieten.
- **Berufe:** Im Spiel bei RaidMaster → Skillungen → **Meine Berufe einlesen**. Danach im Discord:
  `/handwerk Feuerschutz` (wer kann das herstellen?) und `/berufe` (Übersicht) bzw. `/berufe Name`.
- **DKP-Nachricht:** Nach jedem Raid bekommt jeder Teilnehmer mit Discord-Profil eine Direktnachricht: verdient,
  ausgegeben, gewonnene Items, neuer Stand. Abbestellen: `/dkp-nachricht aus`. Ganz ausschalten: `"raid_dms": false`.
- **Verfall:** 10 % jeden Mittwoch nach dem Raid-Reset (bucht das Addon). Die DKP-Liste im Discord zeigt
  „Verfall: 10 % jeden Mittwoch · zuletzt …“.

## Eigene Beute-Datenbank

RaidMaster merkt sich nach jedem Bosskill, welche Items im Lootfenster lagen. Der Uploader schickt das mit,
der Bot führt die Daten aller Uploader zusammen (derselbe Kill zählt nur einmal, gespeichert in `data/loot_db.json`).

- Nach jedem Raid hängt der Bot im **Loot-Kanal** des Raids die **Beutetabelle** an: je Boss die Items mit
  „so oft gedroppt / so oft getötet“ (Droprate). Die alte Tabelle wird dabei gelöscht.
- Darunter die **zufälligen Drops vom Trash** (jede Leiche nur einmal gezählt).
- **Symbole:** Das Addon speichert die Datei-ID des Spielsymbols. Der Bot ordnet sie über die Community-Listfile
  (github.com/wowdev/wow-listfile) dem Symbolnamen zu – auch für neue WoW-Forever-Items. Die Liste wird alle
  14 Tage aktualisiert (`data/icon_fileids.json.gz`); eine Fassung liegt dem Bot bei.
- `/beute boss` – was droppt dieser Boss? (nur für dich sichtbar)
- `/beute entfernen` – falsch erfasstes Item aus der Tabelle eines Bosses nehmen (Offiziere)
- `/beute export` – die ganze Datenbank als Datei (Offiziere)
- `/beute tabellen` – alle Beutetabellen neu posten (Offiziere)
- Ausschalten: `"loot_tables": false` in der config.json (die Daten werden trotzdem gesammelt).

Neue Raids (ab 9. Dezember 2026: Barrow Deeps, Hyjalgipfel, Onyxia) kommen von selbst dazu, sobald ihr dort Bosse tötet.

## Aufstellung und feste Gruppen

`/raid aufstellung raid:<Raid>` (oder automatisch mit der Erinnerung vor dem Raid) postet die
Aufstellung in **#einteilung** und **#offiziere**:

1. **Optimale Besetzung hat Vorrang:** Zuerst Tanks und Heiler nach Bedarf, dann wichtige Klassen,
   dann Nahkampf und Fernkampf. Die Rolle kommt aus dem Profil – und damit aus der Skillung.
2. **Innerhalb jeder Rolle haben Stammspieler Vorrang** (⭐ = mind. 70 % der letzten 10 Raids).
3. **Gruppe 1 = Main- und Offtank** (immer zusammen, Stammspieler zuerst) mit den weiteren Tanks, danach Nahkampf-, Fernkampf- und Heilergruppen.
4. Wer nicht hineinpasst, steht auf der **Ersatzbank**.

Der Knopf **„Für RaidMaster“** exportiert Anmeldungen, Startzeit, die Gruppen und bei PUG-Raids den Einladungslink –
im Spiel lädt das Addon dann automatisch ein und sortiert die Gruppen.
- **Gruppen wie im Classic-Raid:** Gruppe 1 = Tanks, dann Nahkampfgruppen, eine Hexer-Gruppe mit Schattenpriester,
  Magier-Gruppen und eine Jäger-Gruppe. In jede Kampfgruppe kommt ein Schamane (Horde) bzw. Paladin (Allianz),
  weil Totems und Auren nur in der eigenen Gruppe wirken; die übrigen Heiler füllen Heilergruppen und freie Plätze.
  Jede Gruppe ist in der Aufstellung beschriftet (z. B. „Gruppe 2 (Nahkampf)“).

## Testdaten aus dem Test-Tool

Im Test-Tool (`/rmtest`) schickt **„Test an Discord senden“** DKP-Stand, Teilnehmer und Loot des Tests in die
Kanäle des Raids – mit **🧪 TEST** markiert. Der Bot löscht diese Nachrichten nach **10 Minuten** selbst (auch nach
einem Neustart). Daten aus dem Testmodus übernimmt der Bot **nie** als echte DKP – auch nicht, wenn jemand mitten
im Test ausloggt.

## Einteilung als Direktnachricht

Erstellt die Raidleitung im Spiel die **Einteilung** und gibt danach `/reload` ein, postet der Bot die
Übersicht in **#einteilung** und schickt jedem verknüpften Spieler seine Aufgaben als **Direktnachricht**.

## Gildenregeln (Kategorie 📜 REGELN)

- Der Bot legt die Kategorie **📜 REGELN** unter 📌 INFO an – mit den Kanälen #verhaltensregeln, #loot-regeln
  (Looten außerhalb von Raids), #gildenbank und #ränge-und-aufnahme – und postet dort die Regeltexte.
- **Alle lesen, nur Offiziere (Rolle „Offizier“), Admins und der Bot schreiben.** Raidleitung und Mitglieder können
  dort nichts posten, nur reagieren.
- Die Texte stehen in `RaidMasterBot/guild_rules.json`. Wird die Datei geändert (z. B. auf GitHub), ersetzt der Bot
  nach dem nächsten Update seine Beiträge – die Nachrichten bleiben an ihrem Platz. Offiziere können zusätzlich
  eigene Beiträge in die Kanäle schreiben.

## DKP in Discord

- Jeder Raid hat einen eigenen DKP-Topf und einen eigenen Kanal in seiner Kategorie (#mc-dkp usw.).
- **DKP-Kanal = feste DKP-Liste:** je Raid (MC, Onyxia, BWL …) dieselbe Darstellung – Platz, Punkt in Klassenfarbe,
  Name, Klasse, DKP und ggf. „Ersatzbank“, oben die Gesamtsumme. Alle Raids sind zusammengefasst; nach jedem Raid wird
  dieselbe Nachricht bearbeitet (nichts Neues gepostet). Solange ein Raid läuft, bleibt der letzte Stand stehen.
  „Verdient“ wird weiter mitgezählt, aber weder im Discord noch im Addon angezeigt.
- Einzelne Raid-Abrechnungen gibt es standardmäßig nicht mehr (in config.json `"raid_summaries": true` schaltet sie
  wieder ein). Alte Abrechnungen des Bots werden einmal aus den DKP-Kanälen entfernt.
- `/dkp` zeigt die eigenen DKP in allen Raids, `/dkpliste raid:<Raid>` die Rangliste.
- Neue Items erscheinen im Loot-Kanal des jeweiligen Raids (#mc-loot usw.) als kompakte Liste: vorne das echte
  Item-Symbol, dann Uhrzeit, Gewinner (Punkt in Klassenfarbe), Itemname und DKP.
- **Klassenfarben wie im Spiel:** DKP-Stand und Raid-Abrechnung kommen als Bild – Namen und Klassen in der echten
  WoW-Klassenfarbe. Jedes Mitglied bekommt außerdem eine Rolle seiner Klasse (Krieger, Magier …) in der Klassenfarbe,
  so erscheint auch sein Name im Discord farbig. Die Klasse kommt aus dem Profil (Anmeldung/Charakter), sonst wird der
  Discord-Name mit den RaidMaster-Daten abgeglichen. Der Bot braucht dafür **Rollen verwalten**; seine eigene Rolle
  muss in der Rollenliste über den Klassenrollen stehen.
- WoW schreibt die Daten beim **Ausloggen** oder nach **/reload** – der Uploader schickt sie sofort weiter.

## Alle Befehle

| Befehl | Wer | Wofür |
|---|---|---|
| `/raid erstellen` | Offiziere | Raid (DKP oder PUG) zur Anmeldung |
| `/raid aufstellung` | Offiziere | Aufstellung + Gruppen posten |
| `/raid liste`, `schliessen`, `oeffnen`, `absagen`, `export` | Offiziere | Raids verwalten |
| `/raid taktik` | Offiziere | Taktik eines Raids (oder ohne Angabe: aller Raids) in die Taktik-Kanäle (#mc-taktik, #onyxia-taktik …) |
| `/raid softres` | Offiziere | softres.it-Link eines PUG-Raids setzen/ändern |
| `/addon` | alle | Download-Link der aktuellen Addon-Version |
| `/addon-hochladen` | Admins | Addon-ZIP hochladen (RaidMaster → #raid-addon, AH Analyzer Pro → #aktionshaus) |
| `/charakter` | alle | Charakter und Rolle festlegen |
| `/dkp`, `/dkpliste` | alle | DKP abfragen |
| `/raidmaster-status` | Offiziere | Version, Uploads, Datenstand |
| `/raidmaster-einrichten` | Admins | Server einrichten/ergänzen |
| `/uploader` | Admins | Uploader-Programm + Einrichtungsdatei per Direktnachricht (`nur_programm`: nur das Programm) |
| `/pug-einladung` | Offiziere | Einladungslink für PUG-Spieler (Rolle Gast) |
| `/willkommen` | Admins | Willkommenstext neu eintragen, z. B. mit anderem Gildennamen (`gildenname:…`) – sonst macht es der Bot selbst |
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
