"""Quelltext des Bots für Text-Tests (D-3, ab Bot 1.5.146): bot.py wird schrittweise in Module geteilt.

- alle(): bot.py und alle Bot-Module (ohne Tests) hintereinander – für "kommt vor"/"kommt nicht vor"-Prüfungen.
- funktion(name): genau der Quelltext der Funktion/Klasse name (oberste Ebene), egal in welchem Modul sie liegt –
  statt Ausschnitten "von Funktion A bis Funktion B", die beim Verschieben brechen würden.
"""
from __future__ import annotations

import ast
import os

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def dateien() -> list[str]:
    names = sorted(f for f in os.listdir(BOT_DIR) if f.endswith(".py") and f != "bot.py")
    return [os.path.join(BOT_DIR, "bot.py")] + [os.path.join(BOT_DIR, f) for f in names]


def alle() -> str:
    out = []
    for p in dateien():
        with open(p, encoding="utf-8") as f:
            out.append(f"# ==== {os.path.basename(p)} ====\n" + f.read())
    return "\n".join(out)


def funktion(name: str) -> str:
    for p in dateien():
        with open(p, encoding="utf-8") as f:
            src = f.read()
        lines = src.split("\n")
        for n in ast.parse(src).body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name:
                start = (n.decorator_list[0].lineno if n.decorator_list else n.lineno) - 1
                return "\n".join(lines[start:n.end_lineno])
    raise LookupError(f"{name} in keinem Bot-Modul gefunden")
