"""/pn – Gildenleitung schickt einem Mitglied eine Privatnachricht über den Bot (ab Bot 1.5.133, Wunsch des Nutzers
14.11.2026: Uploader-Anleitung per PN vom Discord-Bot).

- Nur Gildenchef und Offiziere (is_creator). Empfänger: ein Mitglied des Servers, nie ein Bot.
- Der Text wird in einem Formular (Modal) geschrieben bzw. aus einer Vorlage vorausgefüllt und vor dem Senden
  angezeigt; der Absender sieht im Formular genau, was geschickt wird.
- Im Protokoll steht nur, DASS eine PN ging (Empfänger-ID, Länge) – nie der Text.
- Keine Dateien, keine Erwähnungen (@everyone/@here/Rollen werden nicht ausgelöst).
Ohne Discord testbar (tests/test_pn.py).
"""
from __future__ import annotations

MAX_LEN = 1900          # Discord-Nachricht: 2000 Zeichen; Platz für den Kopf

VORLAGEN = {
    "uploader": (
        "Hi, so richtest du den Uploader ein:\n\n"
        "1. Das Python-Fenster (\"ist bereits installiert\") einfach mit X schliessen – Python ist schon drauf.\n"
        "2. Uploader herunterladen:\n"
        "   https://github.com/andreasuhlmann78-create/raidmaster/raw/main/download/RaidMasterUploader.zip\n"
        "   Entpacken, den Ordner \"RaidMasterUploader\" z. B. nach Dokumente legen.\n"
        "3. Die Datei uploader_config.json, die ich dir privat geschickt habe, in diesen Ordner legen.\n"
        "   Nie weitergeben – sie enthält einen geheimen Link zu unserem Discord.\n"
        "4. uploader.bat doppelklicken und das Fenster offen lassen. Fragt es nach einer Python-Installation: "
        "Y und Enter.\n"
        "5. Optional Autostart: im selben Ordner \"Autostart-einrichten.bat\" doppelklicken. Dann startet der "
        "Uploader bei jeder Anmeldung automatisch und minimiert.\n\n"
        "Kommt ein Fehler: Bild vom schwarzen Fenster schicken."
    ),
}
VORLAGEN_NAMEN = {"uploader": "Uploader-Anleitung"}


def vorlage(name: str | None) -> str:
    return VORLAGEN.get(name or "", "")


def nachricht(absender: str, text: str, gilde: str | None = None) -> str | None:
    """Fertige PN: kurzer Kopf (wer schickt sie) + Text. None, wenn leer."""
    text = (text or "").strip()
    if not text:
        return None
    kopf = f"✉️ Nachricht von **{absender}**" + (f" (Gildenleitung {gilde})" if gilde else "") + ":\n\n"
    return (kopf + text)[:2000]


def log_line(empfaenger_id: int, text: str) -> str:
    """Protokoll ohne Inhalt."""
    return f"PN an {empfaenger_id} gesendet ({len(text or '')} Zeichen)"
