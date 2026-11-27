## AHSentinel 0.65.422

> Beta-Version. Bitte melde Fehler in den Kommentaren auf CurseForge, am besten mit der Lua-Fehlermeldung und der WoW-Version.
> Beta version. Please report errors in the comments on CurseForge, ideally with the Lua error message and your WoW version.

### Deutsch – das Wichtigste seit 0.65.413

- **Weniger Chat, nur was dir hilft:** beim Einloggen nur noch eine Zeile mit Version ("AHSentinel 0.65.422 – /ahs oder der Münz-Button öffnet das Fenster"). Die Tagesbilanz kommt nur, wenn es etwas zu melden gibt.
- **Fehler:** im Chat nur noch eine kurze Zeile je Sitzung; die Einzelheiten gehen wie bisher in die Fehlerliste.
- **Tipps nur einmal:** Hinweise wie der Raid-Start-Hinweis erscheinen ein einziges Mal und danach nie wieder.
- **Optionen in verständlichen Worten:** das Vollscan-Tempo zeigt "sehr flüssig / flüssig / ausgewogen / schneller" statt Millisekunden; "Preis-Sync" heisst jetzt "Preise teilen".
- **"Lohnt bis"-Abfragen viel schneller (z. B. für ProfessionSentinel):** die Sicherheitsmarge beim Entzaubern hat für jeden früheren Entzauber-Kauf die Item-Daten neu abgefragt (rund 1000-mal) – jetzt einmal je Item. Eine erste Abfrage dauert etwa 1–2 ms statt bis zu 40 ms, mit denselben Werten. Die Buchungsliste wird im Hintergrund vorbereitet.
- **Auktionshaus gleich nach dem Einloggen öffnen ist flüssiger:** der Reiter ist etwa 2 Sekunden nach dem Laden im Hintergrund vorgebaut.
- Mehr Diagnose für langsame Preis-Abfragen anderer Addons (z. B. ProfessionSentinel). Im Testmodus bleibt alles wie bisher sichtbar.

### English – the most important changes since 0.65.413

- **Less chat, only what helps you:** on login just one line with the version ("AHSentinel 0.65.422 – /ahs or the coin button opens the window"). The daily summary only appears when there is something to report.
- **Errors:** in chat only one short line per session; the details still go to the error list.
- **Tips only once:** hints such as the raid start notice are shown a single time and then never again.
- **Options in plain words:** the full scan speed shows "very smooth / smooth / balanced / faster" instead of milliseconds; "price sync" is now called "share prices".
- **Much faster "worth up to" answers (e.g. for ProfessionSentinel):** the disenchanting safety margin looked up the item data of every past disenchant purchase again (about 1000 times) – now once per item. A first question takes about 1–2 ms instead of up to 40 ms, with the same values. The bookings list is prepared in the background.
- **Opening the auction house right after login is smoother:** the tab is pre-built in the background about 2 seconds after loading.
- More diagnostics for slow price questions from other addons (e.g. ProfessionSentinel). In test mode everything stays visible as before.
