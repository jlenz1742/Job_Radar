# -*- coding: utf-8 -*-
"""fetch_jobsch — jobs.ch-Stichwortsuche für eine Firma.

Dokumentierte Fallstricke (siehe README.md), hier eingebaut:
- '+' und '&' im Suchbegriff durch '%20' ersetzen, nicht als '+' kodieren
- kein &sort=, kein &region= (Redirect-Schleifen bzw. zerstoerte Relevanz)
- nur Seite 1 (Seite 2 liefert ueberwiegend Fremdtreffer)
- Trefferliste nach dem tatsaechlichen Arbeitgeber filtern (mischt Fremdfirmen)
"""
import re
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

# Absichtlich KEIN Browser-User-Agent: jobs.ch liefert einem Client, der sich
# als Chrome ausgibt aber kein JS ausfuehrt, einen Satz Koeder-Treffer
# (Fuzzy-Match auf irrelevante Jobs) statt der echten Suche. Mit dem
# Standard-UA von requests kommen die echten Treffer. Gegengeprueft am
# 2026-09-10 — falls das wieder umgekehrt sein sollte, hier zuerst schauen.
HEADERS = {
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
}

def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def fetch_jobsch(firma, suchbegriff=None, timeout=20):
    """Gibt (stellen, fehler) zurueck. stellen nur dort, wo der Arbeitgeber
    tatsaechlich `firma` entspricht (grobe Teilstring-Pruefung, entumlautet)."""
    begriff = (suchbegriff or firma).replace("+", " ").replace("&", " ")
    url = "https://www.jobs.ch/de/stellenangebote/?term=" + quote(begriff, safe="")
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException as e:
        return [], f"FEHLER — {type(e).__name__}"
    if r.status_code >= 400:
        return [], f"FEHLER — HTTP {r.status_code}"

    soup = BeautifulSoup(r.text, "html.parser")
    ziel = _norm(firma)
    stellen, gesehen = [], set()
    for a in soup.find_all("a", attrs={"data-cy": "job-link"}, href=True):
        href = a["href"]
        titel = a.get("title") or a.get_text(" ", strip=True)
        # jobs.ch rendert die ganze Karte (Titel, Ort, Firma) im selben <a>;
        # die Firma steht im letzten fett gesetzten Caption-<p> der Karte.
        # Reihenfolge der Karte: [Alter, Ort, Pensum, Anstellungsart, ..., Firma]
        caption_ps = a.find_all("p", class_="textStyle_caption1")
        firma_karte = caption_ps[-1].get_text(" ", strip=True) if caption_ps else ""
        ort_karte = caption_ps[1].get_text(" ", strip=True) if len(caption_ps) > 1 else ""
        if ziel not in _norm(firma_karte):
            continue
        url_abs = href if href.startswith("http") else "https://www.jobs.ch" + href
        if url_abs in gesehen:
            continue
        gesehen.add(url_abs)
        stellen.append({"titel": titel, "url": url_abs, "ort": ort_karte, "firma_jobsch": firma_karte})
    return stellen, None
