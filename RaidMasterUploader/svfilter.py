"""SavedVariables vor dem Hochladen ins private Daten-Repo bereinigen – ab Uploader 2.3.13 (UP-DS1).

Entscheid des Nutzers 16.11.2026 07:10 (Datenschutz): Bewerber und Sperrliste aus GuildSentinel gehen NICHT ins Daten-Repo.
GuildSentinel speichert je Gilde (GuildSentinelDB.guilds["Realm|Gilde"]):
    apps = { [Name] = { t, msg, c, st } }   – Bewerber mit Nachricht
    ban  = { ... }                           – Sperrliste mit Gründen
Diese beiden Einträge werden in JEDER Gilde durch leere Tabellen ersetzt – nur in der Kopie, die hochgeht. Die Datei im
Spiel bleibt unverändert. Alles andere bleibt Zeichen für Zeichen gleich (nur die beiden Tabelleninhalte werden ersetzt).

Sicher: Die Datei wird mit einem kleinen Lua-Leser vollständig gelesen (Zeichenketten mit Anführungszeichen, Klammern,
Escapes \\" \\\\ \\n \\ddd, Zeilenfortsetzung, lange Zeichenketten [[…]] / [==[…]==], Kommentare). Geht das Lesen schief,
wird die Datei NICHT geliefert (FilterError) – nie ungefiltert.
"""
from __future__ import annotations

GS_DROP = ("apps", "ban")


class FilterError(Exception):
    pass


class _Reader:
    def __init__(self, text: str):
        self.s, self.i, self.n = text, 0, len(text)

    def fail(self, why: str):
        line = self.s.count("\n", 0, self.i) + 1
        raise FilterError(f"{why} (Zeile {line})")

    def skip(self):
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n\f\v":
                self.i += 1
            elif s.startswith("--", self.i):
                j = self.i + 2
                lvl = self._long_level(j)
                if lvl is not None:
                    self.i = j
                    self._long_body(lvl)
                else:
                    k = s.find("\n", j)
                    self.i = n if k < 0 else k + 1
            else:
                return

    def _long_level(self, j: int):
        """[[ oder [==[ an Stelle j -> Anzahl '=' ; sonst None."""
        s = self.s
        if j < self.n and s[j] == "[":
            k = j + 1
            while k < self.n and s[k] == "=":
                k += 1
            if k < self.n and s[k] == "[":
                return k - j - 1
        return None

    def _long_body(self, lvl: int):
        start = self.i
        close = "]" + "=" * lvl + "]"
        self.i += lvl + 2
        k = self.s.find(close, self.i)
        if k < 0:
            self.i = start
            self.fail("lange Zeichenkette ohne Ende")
        self.i = k + len(close)

    def string(self) -> str:
        s = self.s
        q = s[self.i]
        if q == "[":
            lvl = self._long_level(self.i)
            if lvl is None:
                self.fail("unerwartetes [")
            a = self.i + lvl + 2
            self._long_body(lvl)
            body = s[a:self.i - lvl - 2]
            return body[1:] if body.startswith("\n") else body
        self.i += 1
        out = []
        while True:
            if self.i >= self.n:
                self.fail("Zeichenkette ohne Ende")
            c = s[self.i]
            if c == q:
                self.i += 1
                return "".join(out)
            if c == "\n":
                self.fail("Zeilenumbruch in Zeichenkette")
            if c == "\\":
                self.i += 1
                if self.i >= self.n:
                    self.fail("Escape am Dateiende")
                e = s[self.i]
                if e.isdigit():
                    j = self.i
                    while j < self.n and j - self.i < 3 and s[j].isdigit():
                        j += 1
                    out.append(chr(int(s[self.i:j]) & 0xFF))
                    self.i = j
                    continue
                if e == "\r" and s.startswith("\r\n", self.i):
                    self.i += 1
                out.append({"n": "\n", "t": "\t", "r": "\r", "a": "\a", "b": "\b", "f": "\f", "v": "\v",
                            "\n": "\n"}.get(e, e))
                self.i += 1
                continue
            out.append(c)
            self.i += 1

    def name(self) -> str:
        s, j = self.s, self.i
        while j < self.n and (s[j].isalnum() or s[j] == "_"):
            j += 1
        if j == self.i:
            self.fail(f"unerwartetes Zeichen {s[self.i]!r}")
        word, self.i = s[self.i:j], j
        return word

    def number(self):
        s, j = self.s, self.i
        if s[j] == "-":
            j += 1
        k = j
        while k < self.n and (s[k].isalnum() or s[k] in ".+-") and not (s[k] in "+-" and s[k - 1] not in "eEpP"):
            k += 1
        txt = s[self.i:k]
        try:
            v = int(txt, 0) if txt.lstrip("-").lower().startswith("0x") else float(txt)
        except ValueError:
            self.fail(f"Zahl {txt!r} nicht lesbar")
        self.i = k
        return v

    def value(self):
        """Liest einen Wert. Tabellen -> ('table', start, end, [(key, value), ...]); sonst ('atom', start, end, v)."""
        self.skip()
        if self.i >= self.n:
            self.fail("Wert fehlt am Dateiende")
        s, c = self.s, self.s[self.i]
        start = self.i
        if c == "{":
            return self.table()
        if c in "\"'" or (c == "[" and self._long_level(self.i) is not None):
            v = self.string()
            return ("atom", start, self.i, v)
        if c.isdigit() or c == "-" or (c == "." and self.i + 1 < self.n and s[self.i + 1].isdigit()):
            v = self.number()
            return ("atom", start, self.i, v)
        w = self.name()
        if w in ("true", "false", "nil"):
            return ("atom", start, self.i, {"true": True, "false": False, "nil": None}[w])
        self.fail(f"unbekannter Wert {w!r}")

    def table(self):
        start = self.i
        self.i += 1
        items, pos = [], 0
        while True:
            self.skip()
            if self.i >= self.n:
                self.fail("Tabelle ohne Ende")
            c = self.s[self.i]
            if c == "}":
                self.i += 1
                return ("table", start, self.i, items)
            if c == "[" and self._long_level(self.i) is None:
                self.i += 1
                k = self.value()
                self.skip()
                if not self.s.startswith("]", self.i):
                    self.fail("] fehlt")
                self.i += 1
                self.skip()
                if not self.s.startswith("=", self.i):
                    self.fail("= fehlt")
                self.i += 1
                key = k[3] if k[0] == "atom" else None
                items.append((key, self.value()))
            else:
                save = self.i
                if c.isalpha() or c == "_":
                    w = self.name()
                    self.skip()
                    if self.s.startswith("=", self.i) and not self.s.startswith("==", self.i):
                        self.i += 1
                        items.append((w, self.value()))
                    else:
                        self.i = save
                        pos += 1
                        items.append((pos, self.value()))
                else:
                    pos += 1
                    items.append((pos, self.value()))
            self.skip()
            if self.i < self.n and self.s[self.i] in ",;":
                self.i += 1

    def chunk(self) -> dict:
        """Ganze Datei: Folge von  Name = Wert. Rückgabe {Name: Wert-Knoten}."""
        out = {}
        while True:
            self.skip()
            if self.i >= self.n:
                return out
            w = self.name()
            self.skip()
            if not self.s.startswith("=", self.i):
                self.fail("= nach " + w + " fehlt")
            self.i += 1
            out[w] = self.value()


def _get(node, key):
    if node and node[0] == "table":
        for k, v in node[3]:
            if k == key:
                return v
    return None


def filter_guildsentinel(data: bytes) -> tuple[bytes, int]:
    """Bewerber (apps) und Sperrliste (ban) in jeder Gilde leeren. Rückgabe (neue Bytes, Anzahl geleerter Tabellen).
    FilterError, wenn die Datei nicht sicher gelesen werden kann."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise FilterError(f"kein UTF-8 (Byte {e.start})") from None
    top = _Reader(text).chunk()
    db = top.get("GuildSentinelDB")
    if db is None:
        return data, 0
    if db[0] != "table":
        raise FilterError("GuildSentinelDB ist keine Tabelle")
    guilds = _get(db, "guilds")
    spans = []
    if guilds is not None:
        if guilds[0] != "table":
            raise FilterError("guilds ist keine Tabelle")
        for _, g in guilds[3]:
            if g[0] != "table":
                continue
            for key in GS_DROP:
                v = _get(g, key)
                if v is None:
                    continue
                if v[0] == "table":
                    if v[3]:
                        spans.append((v[1], v[2]))
                else:
                    spans.append((v[1], v[2]))          # unerwartete Form (z. B. Text) -> ebenfalls leeren
    if not spans:
        return data, 0
    out, last = [], 0
    for a, b in sorted(spans):
        out.append(text[last:a])
        out.append("{\n}")
        last = b
    out.append(text[last:])
    new = "".join(out)
    _Reader(new).chunk()                                  # Ergebnis muss wieder lesbar sein
    return new.encode("utf-8"), len(spans)
