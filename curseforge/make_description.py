#!/usr/bin/env python3
"""Schreibt den Abschnitt "What's new" der CurseForge-Beschreibung neu - aus dem
CHANGELOG.md der neuesten Zip in download/.

CurseForge hat keine Schnittstelle, um die Projektbeschreibung zu ändern. Deshalb
erzeugt dieses Skript bei jeder neuen Version die fertige Beschreibung
(<Addon>-description.md und .html); die HTML-Datei wird auf CurseForge eingefügt.

Aufruf:  python3 curseforge/make_description.py [Addon-Name ...] [--versions N]
"""
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from upload import newest_zip  # noqa: E402

DEFAULT_VERSIONS = 5


def read_changelog(path, addon):
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.lower() == f"{addon}/changelog.md".lower()), None)
        return z.read(name).decode("utf-8", "replace") if name else ""


def sections(text):
    """[(Version, [Zeilen])] in der Reihenfolge der Datei (neueste zuerst)."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^##\s+v?([\d.]+)\s*$", line)
        if m:
            out.append((m.group(1), []))
        elif out:
            out[-1][1].append(line)
    return out


def whats_new(text, count):
    parts = ["## What's new", ""]
    for version, lines in sections(text)[:count]:
        body = [l for l in lines if not l.startswith(">")]          # Beta-Hinweis steht schon oben
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        if not body:
            continue
        parts.append(f"### Version {version}")
        parts.append("")
        parts.extend(body)
        parts.append("")
    parts.append("*Older versions: see the changelog of each file in the **Files** tab.*")
    parts.append("")
    return "\n".join(parts)


def update(addon, count):
    zip_path = newest_zip(addon)
    if not zip_path:
        print(f"{addon}: keine Zip in download/")
        return False
    text = read_changelog(zip_path, addon)
    if not text:
        print(f"{addon}: kein CHANGELOG.md in {zip_path.name}")
        return False
    md_path = HERE / f"{addon}-description.md"
    if not md_path.exists():
        print(f"{addon}: {md_path.name} fehlt")
        return False
    md = md_path.read_text(encoding="utf-8")
    new_section = whats_new(text, count)
    # Abschnitt "What's new" bis zur nächsten Trennlinie ersetzen
    m = re.search(r"^## What's new\n.*?(?=^---\s*$)", md, flags=re.S | re.M)
    if m:
        md = md[:m.start()] + new_section + "\n" + md[m.end():]
    else:
        # noch keiner da: nach der ersten Trennlinie einfügen
        i = md.find("\n---\n")
        md = md[:i + 5] + "\n" + new_section + "\n---\n" + md[i + 5:] if i >= 0 else md + "\n---\n\n" + new_section
    md_path.write_text(md, encoding="utf-8")
    try:
        import markdown
        html = markdown.markdown(md, extensions=["tables"])
        (HERE / f"{addon}-description.html").write_text(html, encoding="utf-8")
    except ImportError:
        print("Hinweis: Python-Paket 'markdown' fehlt - nur .md geschrieben")
    print(f"{addon}: Beschreibung mit den letzten {count} Versionen aus {zip_path.name} aktualisiert")
    return True


def main():
    args = sys.argv[1:]
    count = DEFAULT_VERSIONS
    if "--versions" in args:
        i = args.index("--versions")
        count = int(args[i + 1])
        del args[i:i + 2]
    addons = args or [p.name[:-len("-description.md")] for p in HERE.glob("*-description.md")]
    for addon in addons:
        update(addon, count)


if __name__ == "__main__":
    main()
