"""Exportiert Texte ohne deutsche Übersetzung (mit Kontext) als JSON zum Übersetzen."""
import json
import re
import sys

sys.path.insert(0, "floop/tools")
from de_status import is_missing_de, units, LETTERS  # noqa: E402

CATALOGS = [
    "Trio/Sources/Localizations/Main/Localizable.xcstrings",
    "Trio/Resources/InfoPlist.xcstrings",
    "OmnipodKit/Localization/Localizable.xcstrings",
]


def english(key, entry, src):
    en = entry.get("localizations", {}).get(src)
    if not en:
        return key, None
    if "variations" in en:
        return key, en["variations"]
    vals = [u.get("value", "") for u in units(en)]
    return (vals[0] if vals else key), None


out = []
for cat in CATALOGS:
    d = json.load(open(cat, encoding="utf-8"))
    src = d.get("sourceLanguage", "en")
    for k, e in d["strings"].items():
        if e.get("extractionState") == "stale" or e.get("shouldTranslate") is False or not LETTERS.search(k):
            continue
        if not is_missing_de(k, e, src):
            continue
        text, variations = english(k, e, src)
        item = {"id": len(out), "cat": cat.split("/")[0], "key": k, "en": text}
        if e.get("comment"):
            item["comment"] = e["comment"]
        if variations:
            item["variations"] = variations
        out.append(item)

json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "Texte exportiert;", sum(1 for i in out if "variations" in i), "mit Pluralformen")
