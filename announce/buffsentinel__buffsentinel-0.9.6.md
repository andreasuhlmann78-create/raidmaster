📦 **BuffSentinel 0.9.6** – klare Forever-Hinweise und mehr Stabilität

• **WoW Forever:** Auch die Seiten „Procs“ und „Cooldowns“ sagen jetzt klar, was geht und was nicht:
  – Im Kampf zeigt BuffSentinel keine Procs, Cooldowns oder Buffs an, weil Forever diese Daten für Addons sperrt.
  – Das Reinigen-Raster ist aus, Procs werden nicht automatisch gelernt.
  – Buff-Erinnerungen vor dem Pull und ausserhalb des Kampfes funktionieren wie bisher, mit Hupe und Ein-Klick-Buff.
• Beschädigte gespeicherte Einstellungen werden beim Laden repariert statt Lua-Fehler auszulösen.
• Forever: Tooltips mit geschützten Spielernamen und Addon-Nachrichten mit geschützten Werten lösen keine Lua-Fehler mehr aus.
• Fehler werden gezählt (`/bsen fehler`) und automatisch an die Prüfung gemeldet – so lassen sich Probleme schneller beheben.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner **BuffSentinel** nach `Interface/AddOns` kopieren (alten Ordner ersetzen). Danach im Spiel `/reload` – sonst läuft noch die alte Version.
