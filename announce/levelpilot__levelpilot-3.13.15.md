📢 **LevelPilot 3.13.15** – Fehler in der virtuellen Reise behoben

• **Kein Lua-Fehler mehr in der virtuellen Reise:** Die Meldung „attempt to yield across metamethod/C-call boundary“ ist weg. Dabei brach manchmal still eine Rechnung ab, z. B. die Prüfung des Wegs zum ersten Ziel. Jetzt rechnet die Reise sie vollständig und trotzdem in kleinen Portionen.
• **Nichts geht verloren:** Wege, die andere Spieler während einer Reise schicken, kommen auch nach einem Abbruch der Reise ins Wegnetz, beim Ausloggen sofort.
• Testroutine: Bricht sie nach dem Zeitlimit ab, speichert sie jetzt einen Teilbericht. Das Zeitlimit ist länger.

**📦 Aktualisieren**
`LevelPilot.zip` nach `Interface/AddOns` entpacken und **LevelPilot** sowie **LevelPilot_Data** ersetzen, dann `/reload`.

- GoldSentinel
