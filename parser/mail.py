# -*- coding: utf-8 -*-
"""
parser/mail.py — Alert-Mails aus dem jobradar-Postfach lesen und ins
Fundformat von radar.py übersetzen.

**Regel 1 aus CLAUDE.md: Das Postfach wird NUR gelesen.** Nichts löschen,
nichts archivieren, nichts als gelesen markieren. Deshalb: IMAP EXAMINE
(readonly=True bei select), nicht SELECT, UND BODY.PEEK[] beim Fetch statt
BODY[] — doppelt abgesichert, weil beides für sich schon reichen würde.

Aufruf:
    IMAP_USER=jan.jobradar@gmail.com IMAP_PASS=<App-Passwort> \\
    python parser/mail.py --seit 1 --out lauf.json

--seit N   nur Mails der letzten N Tage (Default 1)
--out      Zieldatei im Fundformat von radar.py (radar.py ingest liest das direkt)

Erkannte Absender (siehe parser/README.md):
    jobmail@jobs.ch                  — Job-Alert (jobs.ch)
    jobalerts-noreply@linkedin.com    — gespeicherte Job-Suche (LinkedIn)
    jobs-noreply@linkedin.com         — "ähnliche Jobs wie ..." (LinkedIn, Empfehlung)
Alles andere (Newsletter, Willkommens-Mails) wird ignoriert.

Gegen echte Mails aus dem jobradar-Postfach entwickelt (10.09.2026) — siehe
tests/test_mail_parser.py für die Fixtures. Eine Einschränkung, die dort
auch dokumentiert ist: bisher existieren nur "Alert wurde aktiv"-Mails von
jobs.ch, keine laufenden "N neue Jobs"-Digests (die Alerts sind alle neu).
Taucht so eine Mail später mit einem anderen Format auf, muss
parse_jobsch() ggf. nachgezogen werden — nicht raten, sondern die Mail hier
mit dazulegen und den Test erweitern.
"""
import argparse, email, imaplib, json, os, re, sys
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from abruf import kanton_aus_ort  # dieselbe Ort->Kanton-Naeherung wie beim Karriereseiten-Abruf

IMAP_HOST = "imap.gmail.com"

ABSENDER_TYP = {
    "jobmail@jobs.ch": "jobsch",
    "jobalerts-noreply@linkedin.com": "linkedin-alert",
    "jobs-noreply@linkedin.com": "linkedin-empfehlung",
}
# Bekanntes Rauschen, siehe parser/README.md -- wird nicht mal gezaehlt.
RAUSCH_ABSENDER = {"newsletters-noreply@linkedin.com", "willkommen@my.jobs.ch", "no_reply@jobs.ch"}

# ---------------------------------------------------------------- jobs.ch
#
# Format (aus echten Mails, 10.09.2026):
#   Dein Job Alert ist nun aktiv
#   Super! Dein Job Alert für <Suchbegriff> ist nun aktiv. [...]
#
#   - <Titel>, <Firma>, <Ort[, Ort...]>
#     <url>
#
#   - <Titel>, <Firma>, <Ort>
#     <url>
#   [...]
# Wenn der Alert (noch) nichts findet, steht statt der Liste ein Satz wie
# "Momentan enthält deine Suche keine [...]".

JOBSCH_EINTRAG = re.compile(r"^- (.+?)\r?\n[ \t]+(https?://\S+)", re.MULTILINE)
JOBSCH_SUCHBEGRIFF = re.compile(r"Job Alert für[:\s]+(.+?)\s+ist nun aktiv")
JOBSCH_LEER = re.compile(r"enthält deine Suche keine", re.IGNORECASE)

def parse_jobsch(text, betreff):
    m = JOBSCH_SUCHBEGRIFF.search(betreff) or JOBSCH_SUCHBEGRIFF.search(text)
    suchbegriff = m.group(1).strip() if m else "unbekannt"
    if JOBSCH_LEER.search(text):
        return [], suchbegriff  # Alert aktiv, explizit 0 Treffer -- kein Fehler, keine Funde
    funde = []
    for block, url in JOBSCH_EINTRAG.findall(text):
        teile = [t.strip() for t in block.split(",") if t.strip()]
        if len(teile) < 2:
            continue  # nicht im erwarteten "Titel, Firma, Ort[, Ort...]"-Format -- lieber auslassen als raten
        titel, firma = teile[0], teile[1]
        ort = ", ".join(teile[2:])
        funde.append(_fund(firma, titel, ort, "Mail (jobs.ch)",
                            f"jobsch-alert:{suchbegriff}", url))
    return funde, suchbegriff

# ---------------------------------------------------------------- LinkedIn
#
# Format (beide Absender, aus echten Mails, 10.09.2026) -- eine Karte pro
# Treffer, durch eine Trennzeile aus Bindestrichen abgetrennt:
#   <Titel>
#   <Firma>
#   <Ort>
#   [optional: Leerzeile + bis zu 3 Metazeilen wie "3 Kontakte" /
#    "Dieses Unternehmen ist aktiv auf Personalsuche."]
#   Jobangebot ansehen: <url>
# (jobs-noreply laesst die Leerzeile/Metazeilen oft ganz weg -- deshalb
# beides als optional behandeln, nicht als zwei Formate.)

LI_EINTRAG = re.compile(
    r"^([^\n]{3,150})\n([^\n]{2,100})\n([^\n]{2,120})\n(?:.*\n){0,4}?"
    r"Jobangebot ansehen: (https?://\S+)",
    re.MULTILINE,
)

def parse_linkedin(text, quelle_id):
    funde = []
    for titel, firma, ort, url in LI_EINTRAG.findall(text):
        funde.append(_fund(firma, titel, ort, "Mail (LinkedIn)", quelle_id,
                            url.split("?", 1)[0]))
    return funde

# ---------------------------------------------------------------- gemeinsam

def _fund(firma, titel, ort, quelle, quelle_id, url):
    return {
        "firma": firma.strip(), "titel": titel.strip(), "ort": ort.strip(),
        "kanton": kanton_aus_ort(ort),
        "quelle": quelle, "quelle_id": quelle_id, "url": url,
        "publiziert": "", "prio": "", "teil": "2",
        "bewertung": "", "consulting": "", "notiz": "",
    }

def _decode(s):
    if not s:
        return ""
    return "".join(
        p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p
        for p, enc in decode_header(s)
    )

def _body_text(msg):
    """Erst text/plain versuchen, sonst html strippen -- nie raten, wenn
    beides fehlt (dann leerer String, der Aufrufer liefert dann 0 Funde)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(charset, errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html" and not part.get_filename():
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(charset, errors="replace")
                    return re.sub(r"<[^>]+>", "\n", html)
        return ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""

# ---------------------------------------------------------------- IMAP

def hole_mails(seit_tagen):
    user, pw = os.environ.get("IMAP_USER"), os.environ.get("IMAP_PASS")
    if not user or not pw:
        raise RuntimeError("IMAP_USER/IMAP_PASS nicht gesetzt")

    m = imaplib.IMAP4_SSL(IMAP_HOST)
    m.login(user, pw)
    # readonly=True -> IMAP EXAMINE statt SELECT: das Postfach bleibt unveraendert,
    # selbst wenn irgendein Fetch-Aufruf unten versehentlich BODY[] statt
    # BODY.PEEK[] verwenden wuerde.
    m.select("INBOX", readonly=True)
    try:
        seit = (datetime.now() - timedelta(days=seit_tagen)).strftime("%d-%b-%Y")
        _, daten = m.search(None, f'(SINCE "{seit}")')
        ids = daten[0].split()

        funde, quellen = [], {}
        for msg_id in ids:
            _, msg_daten = m.fetch(msg_id, "(BODY.PEEK[])")  # PEEK: setzt kein \Seen
            msg = email.message_from_bytes(msg_daten[0][1])
            absender = parseaddr(msg.get("From", ""))[1].lower()
            if absender not in ABSENDER_TYP:
                continue  # unbekannt/Rauschen -- lieber auslassen als raten

            typ = ABSENDER_TYP[absender]
            text = _body_text(msg)
            if not text:
                continue

            if typ == "jobsch":
                neue, suchbegriff = parse_jobsch(text, _decode(msg.get("Subject", "")))
                qid = f"jobsch-alert:{suchbegriff}"
            else:
                neue = parse_linkedin(text, typ)
                qid = typ
            # Quelle nur eintragen, wenn tatsaechlich eine passende Mail dazu kam --
            # Funkstille heisst "kein neuer Job gemeldet", NICHT "0 Stellen offen".
            quellen[qid] = quellen.get(qid, 0) + len(neue)
            funde.extend(neue)
        return funde, quellen
    finally:
        m.logout()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seit", type=int, default=1, help="Mails der letzten N Tage (Default 1)")
    ap.add_argument("--out", default="lauf_mail.json")
    args = ap.parse_args()

    try:
        funde, quellen = hole_mails(args.seit)
    except Exception as e:
        # Nicht abstuerzen -- IMAP-Login/Netzwerk sind Ausfaelle wie jede
        # andere Quelle. Sichtbar im radar.py-Alarm, aber der Rest des
        # Laufs (Karriereseiten, Excel, Commit) soll trotzdem durchlaufen.
        funde, quellen = [], {"mail-postfach": f"FEHLER — {type(e).__name__}: {e}"[:150]}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"funde": funde, "quellen": quellen}, f, ensure_ascii=False, indent=1)
    print(f"{args.out} geschrieben | {len(funde)} Funde aus {len(quellen)} Alert(s)")
    for qid, n in sorted(quellen.items()):
        print(f"  {qid}: {n}")

if __name__ == "__main__":
    main()
