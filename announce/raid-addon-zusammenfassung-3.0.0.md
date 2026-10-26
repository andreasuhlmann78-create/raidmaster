📢 **RaidMaster 3.0.0 – Zusammenfassung der Neuerungen**
Addon **3.0.0** · Discord-Bot **1.5.51** · Uploader **1.6.0**. Die Datei lädst du hier im Kanal herunter. Den alten Ordner **RaidMaster** ersetzen und `/reload` eingeben. Deine Daten bleiben erhalten.

**🧭 Aufgeräumtes Fenster (3.0.0)**
Statt 13 Knöpfen gibt es nur noch 6 Bereiche mit Reitern oben:
• **DKP**: Stände | Log
• **Beute**: Versteigerung | Loot
• **Raid**: Sitzung & Timer | Anmeldungen | Gruppen | Einteilung | Bosse & Symbole
• **Werbung**: PUG-Raid | Werbung
• **Gilde**: Skillungen & Berufe
• **Einstellungen**: Einstellungen | Discord-Anleitung
Es ist keine Funktion weggefallen. RaidMaster merkt sich in jedem Bereich den zuletzt offenen Reiter.
Raidmitglieder und der Plündermeister sehen nur **DKP** und **Beute**. Die Raidleitung sieht alles.

**⚔️ Im Raid**
• **Boss-Leiste**: Hat der Raidleiter einen Boss im Ziel, setzt ein Klick die Taktik als Schlachtzugwarnung und die Symbole. Auf der Leiste gibt es außerdem Pull, Pause und Bereitschafts-Check.
• **Pull- und Pausen-Timer** für alle, auch mit DBM/BigWigs (`/rm pull 10`, `/rm pause 5`).
• **Bereitschafts-Check**: prüft Fläschchen und Elixiere (ohne Weltbuffs, die es in WoW Forever im Raid nicht gibt).
• **Begrüßung beim Raidstart**: Der Text passt zur Raidzone. Gäste und Spieler von der Ersatzbank werden mit Namen begrüßt.
• **Gruppen einteilen**: übernimmt die Aufstellung aus Discord. Main- und Offtank sind immer in Gruppe 1. Der Raid wird dabei nicht mehr getrennt.
• **Lücken füllen**: holt passende Spieler von der Ersatzbank, dann aus der Gilde, dann über die Gruppensuche. Es werden nie mehr als 40 eingeladen.

**🏆 Ruhmeshalle**
• **Erstkill-Feier**: Fanfare, Schlachtzugwarnung und ein Screenshot, der in #ruhmeshalle gepostet wird.
• **Bestzeiten** für jeden Boss (`/rm rekorde`), dazu **Erfolge** und **Raider des Monats**.

**🎁 Beute & DKP**
• **Eigene Beute-Datenbank**: Boss- und Trash-Drops werden gesammelt, jeder Kill zählt. Die Beute kann bis 30 Minuten nach dem Kill geöffnet werden.
• **Item-Tooltip**: zeigt die Droprate und die bisherigen Preise in DKP.
• **DKP-Verfall automatisch**: jeden Mittwoch 10 %.
• **Twinks** können mit ihrem Main verknüpft werden (`/twink`).
• **Persönliche DKP-Nachricht** nach jedem Raid (abbestellen mit `/dkp-nachricht aus`).

**🏦 Gilde**
• **Berufe-Verzeichnis**: In Skillungen & Berufe auf „Meine Berufe einlesen“ klicken.
• **Gildenbank**: Der Bank-Charakter liest Bank, Post und Gold ein. Den Bestand siehst du in #gildenbank und mit `/bank <Suche>`.

**🧪 Test-Werkzeug** (Knopf „Test“ oder `/rmtest`)
• Neuer Reiter **Ansagen**: Hier kannst du Boss-Leiste, Markierungsleiste, Boss-Ansage, Pull, Pause, Bereitschafts-Check, Begrüßung, Erstkill-Feier, Rekord und Lücken füllen ausprobieren.
• Im Test erscheinen die Ansagen wie im echten Raid, auch die Schlachtzugwarnung in der Bildschirmmitte. Sie sind mit [Test] markiert, nur du siehst sie, und deine Daten werden gesichert.
