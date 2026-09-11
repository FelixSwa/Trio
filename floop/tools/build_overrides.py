"""Führt die Übersetzungsblöcke zu floop/de_overrides.json zusammen und prüft Platzhalter."""
import collections
import json
import os
import re
import sys

TR = "floop/tools/tr"
missing = json.load(open(os.path.join(os.environ["TEMP"], "de_missing.json"), encoding="utf-8"))
by_id = {str(i["id"]): i for i in missing}

tr = {}
for name in ("p1.json", "p2.json", "p3.json"):
    tr.update(json.load(open(os.path.join(TR, name), encoding="utf-8")))

CAT = {
    "Trio": "Trio/Sources/Localizations/Main/Localizable.xcstrings",
    "OmnipodKit": "OmnipodKit/Localization/Localizable.xcstrings",
}
FMT = re.compile(r"%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?(?:ll|l|h)?[@dDuUxXoOfeEgGcCsSpaAF%]")

out = collections.defaultdict(dict)
problems = []


def check(key, en, de):
    norm = lambda t: sorted(re.sub(r"\d+\$", "", f) for f in FMT.findall(t))  # %1$@ == %@
    if norm(en) != norm(de):
        problems.append(f"Platzhalter: {key!r}: EN {FMT.findall(en)} / DE {FMT.findall(de)}")
    if en.count("\n") != de.count("\n"):
        problems.append(f"Zeilenumbrüche: {key!r}: EN {en.count(chr(10))} / DE {de.count(chr(10))}")
    if not de.strip():
        problems.append(f"Leer: {key!r}")


for i in missing:
    sid = str(i["id"])
    if not i["key"].strip() or i["key"] == "NSHumanReadableCopyright":
        continue  # leerer Copyright-Eintrag
    if sid not in tr:
        problems.append(f"Fehlt: #{sid} {i['key'][:60]!r}")
        continue
    check(i["key"], i["en"], tr[sid])
    out[CAT[i["cat"]]][i["key"]] = tr[sid]

extra = set(tr) - set(by_id)
if extra:
    problems.append(f"Unbekannte IDs: {sorted(extra)}")

fix = json.load(open(os.path.join(TR, "fix_existing.json"), encoding="utf-8"))
for k, v in fix.items():
    check(k, k, v)
    out[CAT["Trio"]][k] = v

json.dump(out, open("floop/de_overrides.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print({k: len(v) for k, v in out.items()})
print("\n".join(problems) if problems else "Prüfung ok: alle Platzhalter und Zeilenumbrüche stimmen.")
sys.exit(1 if problems else 0)
