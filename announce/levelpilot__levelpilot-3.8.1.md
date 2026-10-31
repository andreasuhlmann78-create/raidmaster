📢 **LevelPilot 3.8.1** – Flugrouten funktionieren jetzt auch im Spiel

GoldSentinel hat seine echten Spieldaten zum Testen geschickt. Damit war der Grund für die **0 Flüge** im Spieltest schnell gefunden.

**✈ Flüge**
Das Spiel speichert Flugpunkte auf der Flugkarte. Diese Karte konnte LevelPilot nicht immer in echte Positionen umrechnen – dann wurde nie ein Flug geplant.
• LevelPilot eicht die Flugkarte jetzt selbst, mit den Zonennamen der Flugpunkte und den Flugmeistern aus dem Datenpaket
• Alle 19 aufgezeichneten Flugpunkte der Horde in Kalimdor werden auf höchstens 40 Yards genau gefunden
• Beim Öffnen der Flugkarte merkt sich LevelPilot den Flugpunkt, an dem ihr steht, als genauen Bezugspunkt
• Der Selbsttest (`/lp test`) zeigt neu die Zeile **Flüge**: wie viele Flugpunkte verortet und bekannt sind

**🩺 Fehler-Protokoll aufgeräumt**
• Alte Einträge aus 3.4–3.6 standen in der Sprache, die damals eingestellt war (Spanisch, Russisch …). Erledigte Zonen-Meldungen sind weg, der Rest erscheint jetzt in eurer Sprache
• „Kommt nicht näher“ wird nicht mehr gemeldet, solange ihr im Questgebiet Gegner jagt

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`. Einmal die Flugkarte bei einem Flugmeister öffnen, dann `/lp test` – die Zeile „Flüge“ sollte alle eure Flugpunkte zeigen.

- GoldSentinel
