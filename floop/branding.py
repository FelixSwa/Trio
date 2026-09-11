#!/usr/bin/env python3
"""FLoop-Branding: ersetzt "Trio" in allen sichtbaren Texten durch "FLoop".

Läuft beim Bau (build_trio.yml, Schritt "Customize Trio") auf der frischen
Arbeitskopie. Die Quelldateien im Repo bleiben unverändert wie bei Trio, damit
der wöchentliche Abgleich mit nightscout/Trio nie an Konflikten scheitert.

Lokal (z. B. vor einem Xcode-Bau auf dem Mac):  python3 floop/branding.py
Nur prüfen, nichts schreiben:                   python3 floop/branding.py --check

Bewusst NICHT ersetzt werden interne Kennungen (Bundle-ID, App Group,
URL-Schema, Typ- und Dateinamen, Nightscout-"enteredBy" usw.) sowie Links
auf die echte Trio-Dokumentation (triodocs.org, GitHub).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW = "FLoop"

# Links/Domains bleiben unangetastet
PROTECT = re.compile(r"https?://\S+|\b[\w.-]+\.(?:org|com|io|net|md)\b\S*")
# Wortgrenzen nur gegen lateinische Buchstaben/Ziffern prüfen, damit auch
# chinesische/koreanische Texte ("允许Trio", "Trio가") erfasst werden.
_B, _A = r"(?<![A-Za-z0-9_])", r"(?![A-Za-z0-9_])"
RULES = [
    (re.compile(_B + r"Trioneer"), "FLooper"),
    (re.compile(_B + r"Trios" + _A), NEW + "s"),     # dt. Genitiv / Plural
    (re.compile(_B + r"Trio" + _A), NEW),            # Trio, Trio's, Trio-Einstellungen, „Trio“
]

# Wenige sichtbare Texte stehen direkt im Swift-Code (nicht übersetzt).
# Nicht gefundene Stellen werden nur gemeldet, der Bau läuft weiter.
SWIFT_LITERALS = [
    ("Trio/Sources/APS/APSManager.swift",
     'return ("Trio", error.localizedDescription)', 'return ("FLoop", error.localizedDescription)'),
    ("Trio/Sources/Modules/ContactImage/View/AddContactImageSheet.swift",
     '"Trio \\(state.contactImageEntries.count + 1)"', '"FLoop \\(state.contactImageEntries.count + 1)"'),
    ("Trio Watch App/TrioWatchApp.swift",
     '{ "Trio Watch App" }', '{ "FLoop Watch App" }'),
    ("Trio Watch Complication/TrioWatchComplication.swift",
     '.configurationDisplayName("Trio")', '.configurationDisplayName("FLoop")'),
    ("Trio Watch Complication/TrioWatchComplication.swift",
     '.description("Displays Trio app icon as complication")', '.description("Displays FLoop app icon as complication")'),
]


def rebrand(text: str) -> str:
    out, pos = [], 0
    for m in PROTECT.finditer(text):
        out.append(_apply(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_apply(text[pos:]))
    return "".join(out)


def _apply(s: str) -> str:
    for rx, repl in RULES:
        s = rx.sub(repl, s)
    return s


def string_units(node):
    if isinstance(node, dict):
        if isinstance(node.get("stringUnit"), dict):
            yield node["stringUnit"]
        for v in node.values():
            yield from string_units(v)
    elif isinstance(node, list):
        for v in node:
            yield from string_units(v)


def tracked(pattern: str):
    # inkl. Submodule (Pod-Treiber, LoopKit usw.); Testdateien auslassen
    files = subprocess.run(["git", "ls-files", "--recurse-submodules", pattern], cwd=ROOT,
                           capture_output=True, text=True, check=True)
    return [ROOT / f for f in files.stdout.splitlines() if f and not re.search(r"Tests?/", f)]


OVERRIDES = ROOT / "floop" / "de_overrides.json"


def load_overrides():
    """Eigene deutsche Übersetzungen: {Katalogpfad: {Schlüssel: Text}}."""
    return json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}


def do_xcstrings(path: Path, write: bool, de_texts: dict) -> int:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    source = data.get("sourceLanguage", "en")
    strings = data.get("strings", {})
    changed = 0
    # 1. fehlende/verbesserte deutsche Übersetzungen einspielen
    for key, text in de_texts.items():
        entry = strings.get(key)
        if entry is None:
            print(f"  Hinweis: Text nicht mehr vorhanden (Trio hat ihn geändert): {key[:70]!r}")
            continue
        entry.setdefault("localizations", {})["de"] = {"stringUnit": {"state": "translated", "value": text}}
        changed += 1
    # 2. "Trio" -> "FLoop" in allen Sprachen
    for key, entry in strings.items():
        locs = entry.get("localizations", {})
        for unit in string_units(locs):
            v = unit.get("value", "")
            nv = rebrand(v)
            if nv != v:
                unit["value"] = nv
                changed += 1
        # Ohne Eintrag in der Quellsprache zeigt iOS den Schlüssel selbst an
        # (und fällt für fehlende Übersetzungen darauf zurück) -> ergänzen.
        if source not in locs and rebrand(key) != key:
            entry.setdefault("localizations", {})[source] = {
                "stringUnit": {"state": "translated", "value": rebrand(key)}}
            changed += 1
    if changed and write:
        text = json.dumps(data, ensure_ascii=False, indent=2, separators=(",", " : "))
        path.write_text(text + ("\n" if raw.endswith("\n") else ""), encoding="utf-8", newline="\n")
    return changed


STRINGS_LINE = re.compile(r'^(\s*"(?:[^"\\]|\\.)*"\s*=\s*")((?:[^"\\]|\\.)*)(";.*)$')


def do_strings(path: Path, write: bool) -> int:
    raw = path.read_bytes()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
    lines = raw.decode(enc).splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines):
        m = STRINGS_LINE.match(line.rstrip("\r\n"))
        if not m:
            continue
        nv = rebrand(m.group(2))
        if nv != m.group(2):
            end = line[len(line.rstrip("\r\n")):]
            lines[i] = m.group(1) + nv + m.group(3) + end
            changed += 1
    if changed and write:
        path.write_bytes("".join(lines).encode(enc))
    return changed


def do_swift(write: bool) -> int:
    changed = 0
    for rel, old, new in SWIFT_LITERALS:
        p = ROOT / rel
        src = p.read_text(encoding="utf-8") if p.exists() else ""
        if old in src:
            changed += 1
            if write:
                p.write_text(src.replace(old, new), encoding="utf-8", newline="")
        elif new not in src:
            print(f"  Hinweis: Stelle nicht gefunden (Trio hat den Code geändert): {rel}: {old}")
    return changed


def main():
    write = "--check" not in sys.argv
    overrides = load_overrides()
    total = 0
    for f in tracked("*.xcstrings"):
        n = do_xcstrings(f, write, overrides.pop(f.relative_to(ROOT).as_posix(), {}))
        if n:
            print(f"  {n:4d}  {f.relative_to(ROOT)}")
        total += n
    for f in tracked("*.strings"):
        n = do_strings(f, write)
        if n:
            print(f"  {n:4d}  {f.relative_to(ROOT)}")
        total += n
    for cat in overrides:
        print(f"  Hinweis: Katalog für Übersetzungen nicht gefunden: {cat}")
    n = do_swift(write)
    print(f"  {n:4d}  Swift-Texte")
    total += n
    print(("Geändert" if write else "Zu ändern") + f": {total} Texte -> {NEW}")


if __name__ == "__main__":
    main()
