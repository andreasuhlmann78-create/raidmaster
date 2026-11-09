📦 **BuffSentinel 0.9.8** – Fehlerbehebung für WoW Forever

• **Keine Lua-Fehler mehr beim Lesen der Buffs in Forever:** Nach dem Kampf und bei Buff-Änderungen konnte die Meldung „Auras cannot be accessed when secret“ erscheinen. BuffSentinel liest Buffs jetzt nur noch, wenn das Spiel es erlaubt:
  – nicht im Kampf und erst eine halbe Sekunde nach dem Kampf,
  – nicht bei Gruppenmitgliedern oder Zielen, die gerade selbst kämpfen.
• Verweigert das Spiel den Zugriff trotzdem, bleiben die zuletzt bekannten Buffs stehen. So gibt es keine falschen „Buff fehlt“-Warnungen und keinen Lua-Fehler.
• Classic Era, TBC, Wrath, Cata und MoP: unverändert.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner **BuffSentinel** nach `Interface/AddOns` kopieren (alten Ordner ersetzen). Danach im Spiel `/reload` – sonst läuft noch die alte Version.
