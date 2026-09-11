"""Zählt Texte ohne deutsche Übersetzung in allen String-Katalogen (inkl. Submodule)."""
import collections
import json
import re
import subprocess
import sys

KEY = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*=')
LETTERS = re.compile(r"[A-Za-z]{2}")


def units(n):
    if isinstance(n, dict):
        if isinstance(n.get("stringUnit"), dict):
            yield n["stringUnit"]
        for v in n.values():
            yield from units(v)
    elif isinstance(n, list):
        for v in n:
            yield from units(v)


def is_missing_de(key, entry, src):
    de = entry.get("localizations", {}).get("de")
    if not de:
        return True
    us = list(units(de))
    if not us:
        return True
    en = [u.get("value", "") for u in units(entry.get("localizations", {}).get(src, {}))] or [key]
    # Übersetzung fehlt, wenn alle DE-Werte leer sind oder nur das Englische kopieren
    return all(not u.get("value") or (u.get("value") in en and u.get("state") != "translated") for u in us)


def xcstrings_missing(path):
    d = json.load(open(path, encoding="utf-8"))
    src = d.get("sourceLanguage", "en")
    out = []
    total = 0
    for k, e in d.get("strings", {}).items():
        if e.get("extractionState") == "stale" or e.get("shouldTranslate") is False:
            continue
        if not LETTERS.search(k):
            continue
        total += 1
        if is_missing_de(k, e, src):
            out.append(k)
    return total, out


def strings_keys(path):
    raw = open(path, "rb").read()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
    return [m.group(1) for line in raw.decode(enc, errors="replace").splitlines() if (m := KEY.match(line))]


def collect():
    files = subprocess.run(["git", "ls-files", "--recurse-submodules"], capture_output=True, text=True,
                           check=True).stdout.splitlines()
    res = collections.OrderedDict()
    for f in files:
        if f.endswith(".xcstrings") and not re.search(r"Tests?/", f):
            t, miss = xcstrings_missing(f)
            res[f] = (t, miss)
    lp = collections.defaultdict(dict)
    for f in files:
        m = re.match(r"(.*)/([\w-]+)\.lproj/([^/]+\.strings)$", f)
        if m and not re.search(r"Tests?/", f):
            lp[(m.group(1), m.group(3))][m.group(2)] = f
    for (base, name), langs in lp.items():
        b = langs.get("Base") or langs.get("en")
        if not b:
            continue
        bk = [k for k in dict.fromkeys(strings_keys(b)) if LETTERS.search(k)]
        dk = set(strings_keys(langs["de"])) if "de" in langs else set()
        res[f"{b}"] = (len(bk), [k for k in bk if k not in dk])
    return res


if __name__ == "__main__":
    res = collect()
    print(f"{'Datei':88} {'Texte':>6} {'ohne DE':>8} {'Wörter':>7}")
    for f, (t, miss) in res.items():
        if miss:
            print(f"{f[:88]:88} {t:6d} {len(miss):8d} {sum(len(k.split()) for k in miss):7d}")
    if "--dump" in sys.argv:
        json.dump({f: miss for f, (t, miss) in res.items() if miss}, open(sys.argv[-1], "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
