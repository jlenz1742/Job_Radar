# -*- coding: utf-8 -*-
"""fetch_static — Karriereseiten abrufen, die ihre Stellenliste serverseitig
rendern (kein Playwright nötig)."""
import requests
from .extract import stellen_aus_html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
}

def fetch_static(url, timeout=20):
    """Gibt (stellen, fehler) zurück. fehler ist None bei Erfolg,
    sonst ein kurzer Text (für quellen-Status in radar.py)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException as e:
        return [], f"FEHLER — {type(e).__name__}"
    if r.status_code == 403 and "robots" in (r.headers.get("X-Robots-Tag") or ""):
        return [], "FEHLER — robots-gesperrt"
    if r.status_code >= 400:
        return [], f"FEHLER — HTTP {r.status_code}"
    stellen = stellen_aus_html(r.text, r.url)
    if not stellen:
        # Seite kam durch, aber keine Job-Href-Struktur erkannt -- das ist
        # ein Parser-Problem, kein "aktuell keine offenen Stellen" (siehe
        # radar.py-Regel: 0 nur vertrauen, wenn die Quelle sauber lieferte).
        return [], "FEHLER — Struktur nicht erkannt (0 Job-Links gefunden)"
    return stellen, None
