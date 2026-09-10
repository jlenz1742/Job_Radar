# -*- coding: utf-8 -*-
"""fetch_js — Karriereseiten abrufen, die ihre Stellenliste nur per
JavaScript rendern (Workday, Eightfold, SuccessFactors-SPA, ...).

Nutzt den in dieser Umgebung vorinstallierten Headless-Chromium via
Playwright. Ein Browser-Kontext wird pro Lauf wiederverwendet (siehe
BrowserPool), damit nicht für jede der 14 Firmen neu gestartet wird.
"""
import os
from playwright.sync_api import sync_playwright
from .extract import stellen_aus_html

BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
# Die vorinstallierte Chromium-Version dieser Umgebung ist aelter als das
# pip-Paket playwright erwartet ("playwright install" NICHT ausfuehren,
# das laedt eine neue, doppelte Kopie herunter) -- deshalb Pfad fest verdrahtet.
CHROMIUM_BIN = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# Bekannte Cookie-Consent-Systeme (OneTrust, Cookiebot, Usercentrics,
# Sourcepoint, ...) haben stabile IDs -- die zuerst versuchen (schnell,
# praezise), danach Text-Suche als Rueckfall fuer alles Custom-Gebaute.
# Manche CMPs haengen ihr Banner in ein IFrame, deshalb ueber page.frames
# iterieren, nicht nur den Hauptframe pruefen.
COOKIE_SELEKTOREN = [
    "#onetrust-accept-btn-handler",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept",
    "[data-testid='uc-accept-all-button']",
    ".sp_choice_type_11",
    "button[aria-label='Accept all']",
    "button[aria-label='Alle akzeptieren']",
    "#accept-cookies", "#cookie-accept", "#gdpr-accept", "#consent-accept",
]
COOKIE_TEXTE = [
    "Accept All", "Accept all", "Accept", "Alle akzeptieren", "Akzeptieren",
    "Zustimmen", "Einverstanden", "Verstanden", "I Agree", "I agree",
    "Alle Cookies akzeptieren", "Allow all", "Allow all cookies",
    "Alle zulassen", "Got it", "Ich stimme zu",
]

def _cookie_banner_wegklicken(page):
    """True, wenn irgendwo ein Cookie-Banner gefunden und weggeklickt wurde."""
    rahmen = [page] + page.frames
    for f in rahmen:
        for sel in COOKIE_SELEKTOREN:
            try:
                f.locator(sel).first.click(timeout=600)
                return True
            except Exception:
                continue
        for text in COOKIE_TEXTE:
            try:
                f.get_by_text(text, exact=False).first.click(timeout=600)
                return True
            except Exception:
                continue
    return False

class BrowserPool:
    """Ein Chromium-Prozess für alle JS-Abrufe eines Laufs."""
    def __enter__(self):
        self._pw = sync_playwright().start()
        launch_kwargs = {"headless": True}
        if os.path.exists(CHROMIUM_BIN):
            launch_kwargs["executable_path"] = CHROMIUM_BIN
        # Chromium liest HTTPS_PROXY nicht selbst -- die Session-Proxy-Adresse
        # muss explizit uebergeben werden, sonst ERR_CONNECTION_RESET.
        https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if https_proxy:
            launch_kwargs["proxy"] = {"server": https_proxy}
        self.browser = self._pw.chromium.launch(**launch_kwargs)
        return self

    def __exit__(self, *exc):
        self.browser.close()
        self._pw.stop()

    def fetch(self, url, warten_auf=None, timeout=25000):
        """Gibt (stellen, fehler) zurück."""
        page = self.browser.new_page(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
            locale="de-CH",
        )
        try:
            page.goto(url, timeout=timeout, wait_until="networkidle")
            _cookie_banner_wegklicken(page)
            if warten_auf:
                try:
                    page.wait_for_selector(warten_auf, timeout=timeout)
                except Exception:
                    pass
            else:
                page.wait_for_timeout(2500)  # Nachladen nach dem ersten Render
            # Eightfold & Co. laden ihre Stellenliste oft erst beim Scrollen
            # nach (Lazy Loading/Virtualisierung) -- einmal runter, kurz warten.
            try:
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(1500)
            except Exception:
                pass
            html = page.content()
        except Exception as e:
            return [], f"FEHLER — {type(e).__name__}: {e}"[:120]
        finally:
            page.close()
        stellen = stellen_aus_html(html, url)
        if not stellen:
            return [], "FEHLER — nach Rendern keine Treffer (Cookie-Wall/Login/leer?)"
        return stellen, None


def fetch_js(url, warten_auf=None):
    """Einzelabruf ohne Pool (Komfortfunktion, startet einen eigenen Browser)."""
    with BrowserPool() as pool:
        return pool.fetch(url, warten_auf=warten_auf)
