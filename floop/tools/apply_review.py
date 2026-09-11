"""Übernimmt die geprüften Korrekturen (Codex-Review 11.09.2026, von Claude bewertet) in die Übersetzungsblöcke."""
import json
import os

TR = "floop/tools/tr"
idx = json.load(open(os.path.join(os.environ["TEMP"], "review_idx.json"), encoding="utf-8"))
missing = json.load(open(os.path.join(os.environ["TEMP"], "de_missing.json"), encoding="utf-8"))
id_by_key = {i["key"]: str(i["id"]) for i in missing}

# Korrekturen nach Nummer in review_de.md
BY_REVIEW = {
    24: "Bitte stelle über WLAN oder mobile Daten eine Internetverbindung her und versuche es erneut.",
    28: "Prüfanfrage vom Server wird angefordert …",
    38: "Der Schlüsselverwaltungs-Server ist vorübergehend nicht verfügbar.",
    39: "Der Schlüsselverwaltungs-Server ist vorübergehend nicht verfügbar: unerwartete Antwort erhalten.",
    46: "Gerätewarnungen (%@)",
    58: "Füge Dein Garmin-Gerät über Garmin Connect zu FLoop hinzu. Wenn Du dasselbe Garmin-Gerät mit Garmin Connect auf mehreren Telefonen verwendest, kommt es je nach Nähe der Telefone zu Verbindungsproblemen zwischen Uhr und Telefon. Das kann auch die Funktion Deines Zifferblatts beeinträchtigen.",
    62: "Füge Deinen iOS-Kontakten einen oder mehrere Kontakte hinzu, um Echtzeitdaten von FLoop auf Deinem Zifferblatt anzuzeigen. Gewähre FLoop vollen Zugriff auf Deine Kontakte, wenn Du dazu aufgefordert wirst.",
    67: "Alle Glukose-, Insulin- und Kohlenhydratdaten. Alle Therapieeinstellungen (Basalrate, ISF, KH-Faktor, Glukoseziele). Deine Nightscout-URL und Dein API-Token. Deine Tidepool-Zugangsdaten. Geheime Schlüssel für Fernbefehle und APNS-Schlüssel. Standortdaten. Protokolle werden nie automatisch gesendet; Du entscheidest selbst, ob Du sie teilst.",
    90: "Die Kohlenhydrate wurden gespeichert. Die Authentifizierung ist fehlgeschlagen, der Bolus wurde nicht abgegeben.",
    98: "Löscht den lokalen App-Attest-Schlüssel sowie die Markierungen „registriert“ und „gesperrt“. Vor dem nächsten Senden von Telemetriedaten wird die App-Attest-Prüfung komplett neu durchgeführt. Nur verwenden, wenn die Telemetrie festhängt.",
    102: "Bestätigungstöne",
    106: "Authentifizierung fehlgeschlagen",
    143: "Wird ausgelöst, wenn die Glukose den Grenzwert für niedrige Glukose erreicht oder unterschreitet.",
    144: "Wird ausgelöst, wenn die Glukose den Grenzwert für dringend niedrige Glukose erreicht oder unterschreitet.",
    148: "Wird ausgelöst, wenn die Glukose den Grenzwert für hohe Glukose erreicht oder überschreitet.",
    185: "Halte die +-Taste auf dem Startbildschirm gedrückt, um die Schnellauswahl-Behandlungen zu öffnen.",
    203: "Keine IOB-Daten verfügbar; die Basalrate kann nicht bestimmt werden.",
    207: "Kein Glukosestatus verfügbar; die Basalrate kann nicht bestimmt werden.",
    208: "Kein Profil verfügbar; die Basalrate kann nicht bestimmt werden.",
    227: "Optional mit Nightscout synchronisieren und die wichtigsten Angaben eintragen.",
    232: "Wähle eine Dauer, für die alle FLoop-Alarme pausiert werden. Kritische Warnungen (z. B. Verschluss, dringend niedrige Glukose) kommen trotz Pause durch.",
    241: "Die Uhrzeit der Pumpe weicht von der Uhrzeit Deines Telefons ab. Zum Prüfen tippen.",
    262: "Szenario für den Sensor-Lebenszyklus",
    295: "Insulinabgabe wird unterbrochen …",
    299: "Tippen, um einen per Fingerstich gemessenen Glukosewert hinzuzufügen.",
    301: "Um Dein Garmin-Gerät mit FLoop zu verwenden, muss die App Garmin Connect installiert sein.\nLade sie im App Store herunter.",
    315: "Verteilungsdiagramm Zeit im Zielbereich",
    317: "Um festzulegen, wann Alarme ausgelöst werden (dringend niedrig / niedrig / hoch / vorhergesagt niedrig), öffne die Glukosealarme.",
    331: "Dringend niedrig",
    333: "Grenzwert dringend niedrig",
    336: "Verwendet die relativ gängige Definition der „Zeit im engen Zielbereich“: den Zeitanteil, in dem die Glukose zwischen %1$@ und %2$@ %3$@ liegt.",
}

# „Snooze“ einheitlich als „pausieren“ (nach Schlüssel)
BY_KEY = {
    "End Snooze": "Pause beenden",
    "Opens snooze options": "Öffnet die Pausen-Optionen",
    "Snooze": "Pausieren",
    "Snooze (15 min)": "Pausieren (15 Min.)",
    "Snooze 1 hr": "1 Std. pausieren",
    "Snooze 3 hrs": "3 Std. pausieren",
    "Snooze 6 hrs": "6 Std. pausieren",
    "Snooze 15 min": "15 Min. pausieren",
    "Snooze alerts": "Alarme pausieren",
    "Snooze all (15 min)": "Alle pausieren (15 Min.)",
    "Snooze All Alarms": "Alle Alarme pausieren",
    "Snoozed until %@": "Pausiert bis %@",
    "snoozed, %d minutes remaining": "pausiert, noch %d Minuten",
    "Swipe left to end snooze.": "Nach links wischen, um die Pause zu beenden.",
    "Urgent Low Glucose": "Dringend niedrige Glukose",
    "will snooze for %@ until %@": "wird für %@ pausiert, bis %@",
}

for n, text in BY_REVIEW.items():
    BY_KEY[idx[n - 1][1]] = text

# Werktage -> Montag bis Freitag (Absätze bleiben erhalten)
WEEK = {
    "Werktage und Wochenenden werden getrennt betrachtet": "Montag bis Freitag und das Wochenende werden getrennt betrachtet",
    "Sie schlägt bis zu drei": "Diese schlägt bis zu drei",
    "gewichtet nach Aktualität und Tagesart (Werktag oder Wochenende)": "gewichtet nach Aktualität und Tagesart (Montag bis Freitag oder Wochenende)",
}

parts = {name: json.load(open(os.path.join(TR, name), encoding="utf-8")) for name in ("p1.json", "p2.json", "p3.json")}
fix = json.load(open(os.path.join(TR, "fix_existing.json"), encoding="utf-8"))
done = 0
for key, text in BY_KEY.items():
    sid = id_by_key.get(key)
    target = next((p for p in parts.values() if sid in p), None) if sid else None
    if target is not None:
        target[sid] = text
    else:
        fix[key] = text  # vorhandene Übersetzung korrigieren
    done += 1
for p in parts.values():
    for sid, v in p.items():
        for a, b in WEEK.items():
            if a in v:
                p[sid] = v = v.replace(a, b)
                done += 1

for name, p in parts.items():
    json.dump(p, open(os.path.join(TR, name), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(fix, open(os.path.join(TR, "fix_existing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("Korrekturen übernommen:", done)
