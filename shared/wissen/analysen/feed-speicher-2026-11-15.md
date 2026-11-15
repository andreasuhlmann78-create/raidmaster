# Feed-Speicher AHSentinel -> GoldSentinelMarkt (Supervisor, 15.11.2026 20:25) – BELEGT

Anlass: AHS-Bericht 0.65.218 (20:13): s216_feed_memory "Feed-Anteil" Median 5 845 KB > Grenze 4 096 -> FEED_ON bleibt aus.
Stand: ahanalyzerpro 6acff97 (0.65.218, GoldSentinelMarkt v7), Lua 5.1 (/usr/bin/lua5.1), 6000 Items.

## 1. s216 hier nachgemessen (unverändert, 6 Durchgänge)
Feed-Anteil = Lauf 4 − Mittel(Lauf 3, 5): −4 895 · −5 284 · −5 096 · −4 687 · −5 837 · −7 754 KB (immer NEGATIV).
Längster Frame mit Feed 18–58 ms, ohne 81–88 ms. -> Die Methode misst hier etwas anderes als bei AHS (dort +3,1 … +7,0 MB).

## 2. Ursache: Grundlinie im Nachbau falsch (Code belegt)
- GoldSentinelMarkt.lua:273 M.OnReplicate: ist AHSentinel geladen (M.api.ahs(), :126 IsAddOnLoaded("AHSentinel")), liest
  GoldSentinelMarkt den Scan NICHT selbst ("ahsentinel liest selbst").
- Der Nachbau definiert IsAddOnLoaded nicht (common.lua:129 nur in der Liste erlaubter Globale) -> ahs() = falsch -> bei Feed AUS
  liest GoldSentinelMarkt den ganzen Scan zusätzlich selbst: 37–54 Ticks mit Leser, 9,3–10,4 MB in GoldSentinelMarkt.Tick.
  Im Spiel passiert das nie. Die Läufe "ohne Feed" sind darum im Nachbau zu teuer, der Unterschied zufällig (Speicherbereinigung,
  wachsender Preisverlauf: Lauf 1–5 schwanken um 10–20 MB) – weder das Minus hier noch das Plus bei AHS ist der Feed-Anteil.

## 3. Direkt gemessen (s216x_feed_direct, AHS_LOADED=1 wie im Spiel, 2 Durchgänge, gleiche Werte)
| Lauf | Feed | in VS:FeedNet | davon GM.Feed | in GoldSentinelMarkt.Tick | Feed gesamt |
|---|---|---|---|---|---|
| L1/L3/L5 | aus | 0 | 0 | 0–166 KB | – |
| L2 (erster Feed, legt Tabellen an) | an | 1 864 KB | 130 | 2 809–2 813 KB | 4 673 KB |
| L4 | an | 1 543 KB | 129 | 1 232 KB | 2 775 KB |
| L6 | an | 1 543 KB | 129 | 2 297 KB | 3 840 KB |
-> Der Feed legt je Scan 2,8–3,8 MB an (ab dem 2. Feed), also UNTER der Grenze 4 MB – aber knapp.
- 1,4 MB davon legt AHSentinel selbst an: Vollscan.lua VS:FeedNet setzt erst alle items[k] = nil und baut dann für jedes Item
  eine NEUE Tabelle (`items[id] or {}` findet nach dem Leeren nie eine alte) – 6000 Tabellen je Scan. Wiederverwenden (nur Felder
  überschreiben, nicht mehr vorhandene Items entfernen) spart ~1,4 MB -> Feed ~1,4–2,4 MB.
- Rest (1,2–2,3 MB in Tick) = Export-Zeile (≤ 1,5 MB, wird gebraucht) + Vergleich/Abgänge; Schwankung L4/L6 ist Verdacht, zu
  messen (wahrscheinlich TrimExport/Export-Liste).

## 4. Folgerung (Auftrag an AHS in offen-ahsentinel.txt, FEED-1)
1. s216 im Nachbau richtigstellen: IsAddOnLoaded("AHSentinel") = wahr (wie im Spiel); Feed-Anteil DIREKT messen (wie s216x).
2. VS:FeedNet Tabellen wiederverwenden.
3. Grenze ≤ 4 MB und Frame ≤ ohne + 5 ms erfüllt (Frame mit Feed hier sogar kürzer) -> VS.FEED_ON = true.
NUTZEN: Mit Feed AUS gibt ein AHSentinel-Spieler heute KEINE Marktdaten ans Netz (GoldSentinelMarkt liest bei geladenem AHS nicht
selbst) – mit Feed AN nutzen AHS Phase 2, PS und alle anderen die Scans der Gilde.

## 5. Nachtrag 20:49 – Schwankung in GoldSentinelMarkt.Tick (L4 1 232 KB, L6 2 298 KB)
Gemessen (Kopie von 0.65.220 mit Zählern in FeedFinish, nichts im Repo geändert): in L2/L4/L6 gleich viele Items (6 108: A 500,
B 5 608, dt 905 s), L4 und L6 je 0 geänderte Preise (keine Weitergabe an die Gilde ausser Pump 0–101 KB), Export 2/4/6 Zeilen.
Die Arbeit ist also in L4 und L6 dieselbe. AHS misst in L8 wieder 1 361 KB (= L4). -> Kein Mehraufwand je Scan; die ~1 MB in
genau einem Lauf passen zum einmaligen Wachsen der internen Zeichenketten-Tabelle von Lua (Verdacht, nicht weiter gemessen –
einmalig, keine Wirkung auf die Grenze). Gleichbleibend je Scan: ~1,2–1,4 MB. Kein GoldSentinelMarkt v8 nötig.
