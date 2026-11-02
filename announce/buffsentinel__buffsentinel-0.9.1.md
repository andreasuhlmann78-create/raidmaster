📦 **BuffSentinel 0.9.1** – fit für WoW Forever

WoW Forever sieht aus wie Classic, läuft aber auf dem **modernen Client mit denselben Addon-Sperren wie Retail**: kein Kampflog, und im Kampf kommen Buffs, Abklingzeiten, Lebenspunkte und Namen nur noch als „geheime Werte“. Damit es zum Start keine Lua-Fehler gibt, behandelt BuffSentinel Forever jetzt genauso wie Retail:

• **Buff-Erinnerungen vor dem Pull** und ausserhalb des Kampfes wie gewohnt, inklusive Hupe und Ein-Klick-Buff.
• **Im Kampf** wertet BuffSentinel auf Forever nichts aus. Beim ersten Kampf kommt ein einmaliger Hinweis: Für Procs im Kampf den **Cooldown Manager des Spiels** nutzen.
• Vor dem Kampf werden alle Buttons versteckt, damit keine unsichtbaren Buttons Klicks abfangen.
• Geheime Werte werden überall geprüft, bevor gerechnet wird: kein falsches Aufleuchten beim Pull, keine Fehler bei Hinrichten, Gruppennamen oder Reinigen.
• Fehler frieren die Anzeige nicht mehr ein. Neuer Befehl `/bsen fehler` zeigt eine kurze Diagnose.

**Classic Era, TBC, Wrath, Cata und MoP Classic laufen unverändert** mit Procs, Cooldowns und Reinigen im Kampf.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner **BuffSentinel** nach `Interface/AddOns` kopieren (alten Ordner ersetzen). Danach im Spiel `/reload` – sonst läuft noch die alte Version.
