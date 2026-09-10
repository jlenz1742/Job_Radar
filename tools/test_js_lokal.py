# -*- coding: utf-8 -*-
"""
test_js_lokal.py — einmaliger Check, ob der Playwright-Pfad (fuer die
JS-only-Karriereseiten) auf DEINEM Rechner funktioniert.

Hintergrund: In der Cloud-Sandbox, in der abruf.py entwickelt wurde, blockiert
der Session-Proxy den HTTPS-Tunnel von Headless-Chromium (ERR_CONNECTION_RESET,
selbst zu example.com -- plain HTTP und curl/requests sind nicht betroffen).
Auf einem normalen Rechner ohne so einen Proxy sollte das nicht auftreten,
aber das muss einmal echt geprueft werden, bevor du dich drauf verlaesst.

Aufruf:
    pip install -r requirements.txt
    playwright install chromium      # laedt den Browser fuer Playwright herunter
    python tools/test_js_lokal.py
"""
import sys, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from fetch.js_page import BrowserPool

# Eine kleine, repraesentative Auswahl der 15 JS-only-Firmen -- reicht, um zu
# sehen, ob der Mechanismus grundsaetzlich funktioniert, ohne alle 15 laufen
# zu lassen.
TESTS = {
    "Amcor (Workday)": "https://amcor.wd5.myworkdayjobs.com/Amcor_External_Career_Site",
    "Alcon (Workday)": "https://alcon.wd5.myworkdayjobs.com/careers_alcon",
    "Kardex (Workday)": "https://kardex.wd103.myworkdayjobs.com/Kardex",
    "STMicroelectronics (Eightfold)": "https://stmicroelectronics.eightfold.ai/careers",
}

def main():
    print("Teste Playwright/Headless-Chromium gegen 4 JS-only-Karriereseiten...\n")
    ok, fehler = 0, 0
    with BrowserPool() as pool:
        for name, url in TESTS.items():
            stellen, err = pool.fetch(url)
            if err:
                print(f"FEHLER  {name}: {err}")
                fehler += 1
            else:
                print(f"OK      {name}: {len(stellen)} Treffer (z.B. \"{stellen[0]['titel'][:60]}\")")
                ok += 1
    print(f"\n{ok} von {len(TESTS)} funktionieren.")
    if ok == 0:
        print("\nAlle 4 sind fehlgeschlagen -- pruef zuerst, ob dein Netzwerk/Proxy")
        print("das Problem ist, nicht der Code:")
        print("  python -c \"from playwright.sync_api import sync_playwright as s; "
              "b=s().start().chromium.launch(); p=b.new_page(); "
              "p.goto('https://example.com'); print(p.title())\"")
    elif fehler:
        print("\nEinige sind fehlgeschlagen -- das kann an der jeweiligen Seite liegen")
        print("(Layout geaendert, Cookie-Banner-Text nicht erkannt), nicht am Mechanismus.")
    else:
        print("\nDer JS-Pfad funktioniert. abruf.py run --prio 1 (ohne --kein-js)")
        print("sollte jetzt auch die restlichen 11 JS-only-Firmen mitnehmen.")

if __name__ == "__main__":
    main()
