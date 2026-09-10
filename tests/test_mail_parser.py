# -*- coding: utf-8 -*-
"""
test_mail_parser.py — prüft parser/mail.py gegen echte Mail-Inhalte aus dem
jobradar-Postfach (10.09.2026, Text unverändert bis auf gekürzte
Tracking-Parameter in den URLs).

Kein IMAP nötig -- testet nur die reine Text-Parsing-Logik.

Aufruf:
    python tests/test_mail_parser.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from parser.mail import parse_jobsch, parse_linkedin

FIXTURES = os.path.join(HERE, "fixtures")

def lesen(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()

def check(bezeichnung, bedingung):
    status = "OK  " if bedingung else "FAIL"
    print(f"{status} {bezeichnung}")
    return bedingung

def main():
    alle_ok = True

    # --- jobs.ch: Alert mit Treffern ---
    text = lesen("jobsch_aktiv.txt")
    funde, suchbegriff = parse_jobsch(text, "Dein Job Alert für: Beratung / Unternehmensentwicklung ist nun aktiv")
    alle_ok &= check("jobsch: Suchbegriff korrekt", suchbegriff == "Beratung / Unternehmensentwicklung")
    alle_ok &= check("jobsch: 3 Funde", len(funde) == 3)
    if funde:
        alle_ok &= check("jobsch: Titel korrekt", funde[0]["titel"] == "Technischer Sales Manager / Verkäufer Aussendienst (m/w/d)")
        alle_ok &= check("jobsch: Firma korrekt", funde[0]["firma"] == "PETRAG HR AG")
        alle_ok &= check("jobsch: Ort korrekt (mehrere Orte)", funde[0]["ort"] == "Schaffhausen, Thurgau, Winterthur")
        alle_ok &= check("jobsch: Kanton erkannt", funde[0]["kanton"] == "SH")
        alle_ok &= check("jobsch: URL korrekt", funde[0]["url"].startswith("https://www.jobs.ch/de/stellenangebote/detail/e0d270b3"))
        alle_ok &= check("jobsch: quelle_id korrekt", funde[0]["quelle_id"] == "jobsch-alert:Beratung / Unternehmensentwicklung")
        alle_ok &= check("jobsch: einfacher Ort ohne Kanton-Zusatz", funde[1]["ort"] == "Langenthal")

    # --- jobs.ch: Alert (noch) ohne Treffer ---
    text = lesen("jobsch_leer.txt")
    funde, suchbegriff = parse_jobsch(text, "Dein Job Alert für: Strategy & Planning Manager ist nun aktiv")
    alle_ok &= check("jobsch (leer): 0 Funde, kein Fehler", funde == [])
    alle_ok &= check("jobsch (leer): Suchbegriff trotzdem erkannt", suchbegriff == "Strategy & Planning Manager")

    # --- LinkedIn: gespeicherte Suche, Digest-Format mit Metazeile ---
    text = lesen("linkedin_alert_digest.txt")
    funde = parse_linkedin(text, "linkedin-alert")
    alle_ok &= check("linkedin (alert): 3 Funde", len(funde) == 3)
    if funde:
        alle_ok &= check("linkedin (alert): Titel korrekt", funde[0]["titel"] == "Senior Project Manager (80-100%)")
        alle_ok &= check("linkedin (alert): Firma korrekt", funde[0]["firma"] == "Belimo")
        alle_ok &= check("linkedin (alert): Ort korrekt", funde[0]["ort"] == "Hinwil, Zürich, Schweiz")
        alle_ok &= check("linkedin (alert): Kanton erkannt", funde[0]["kanton"] == "ZH")
        alle_ok &= check("linkedin (alert): Tracking-Parameter abgeschnitten",
                          funde[0]["url"] == "https://www.linkedin.com/comm/jobs/view/4385917487")
        alle_ok &= check("linkedin (alert): quelle_id korrekt", funde[0]["quelle_id"] == "linkedin-alert")

    # --- LinkedIn: Empfehlungsmail, ohne Metazeile/Leerzeile vor "Jobangebot ansehen" ---
    text = lesen("linkedin_empfehlung.txt")
    funde = parse_linkedin(text, "linkedin-empfehlung")
    alle_ok &= check("linkedin (empfehlung): 3 Funde", len(funde) == 3)
    if funde:
        alle_ok &= check("linkedin (empfehlung): Titel korrekt",
                          funde[0]["titel"] == "Country Head State Street Switzerland, SVP (Senior Managing Director)")
        alle_ok &= check("linkedin (empfehlung): Firma korrekt", funde[0]["firma"] == "State Street")
        alle_ok &= check("linkedin (empfehlung): Ort korrekt", funde[0]["ort"] == "Zürich")
        alle_ok &= check("linkedin (empfehlung): quelle_id korrekt", funde[0]["quelle_id"] == "linkedin-empfehlung")

    print()
    if alle_ok:
        print("Alle Tests bestanden.")
    else:
        print("MINDESTENS EIN TEST FEHLGESCHLAGEN.")
    sys.exit(0 if alle_ok else 1)

if __name__ == "__main__":
    main()
