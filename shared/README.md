# Gemeinsame Dateien für alle GoldSentinel-Addons

| Datei | Zweck |
|---|---|
| `GoldSentinelGame.lua` | Einheitliche Versionserkennung: `GoldSentinelGame.flavor` ("era", "forever", "tbc", "wrath", "cata", "mists", "retail"), `IsForever`, `IsEra`, `IsTBC`, `IsRetail`, `IsModern`, `IsSecret(v)`, `Safe(v)`, `ProperName(name)`, `SameName(a, b, isUnique)` |
| `test_GoldSentinelGame.lua` | Test dazu (Lua 5.1, aus diesem Ordner aufrufen) |

So einbauen (wie `GoldSentinelDev.lua`):
1. `GoldSentinelGame.lua` in den Addon-Ordner kopieren.
2. In der `.toc` **vor** den eigenen Dateien eintragen.
3. Mehrere Addons dürfen die Datei gleichzeitig mitbringen – die neueste Version (`VERSION`) gewinnt.
4. Die eigene Erkennung darauf umstellen, z. B. `local isForever = GoldSentinelGame.IsForever`, mit eigenem Rückfall, falls die Datei fehlt.

Neue Fassung: `VERSION` erhöhen, nur Funktionen ergänzen (nie entfernen oder umbenennen), dann in alle Addons kopieren.
Erster Nutzer: GuildSentinel ab 0.9.6.
