# -*- coding: utf-8 -*-
"""
extract.py — generische Heuristik: aus gerendertem HTML plausible
Stellenanzeigen (Titel + Link) herausziehen.

Kein Karriereseiten-Layout ist wie das andere. Das hier ist bewusst ein
generischer erster Wurf (Link-Text-Heuristik), kein Parser pro ATS-System.
Er funktioniert brauchbar auf serverseitig gerenderten Listen (SmartRecruiters,
Umantis, viele Konzern-Suchen) und nach dem Rendern auch auf JS-Seiten
(Workday, Eightfold) — aber nicht perfekt. Wo die Treffer offensichtlich
daneben liegen, lohnt sich ein eigener Extractor für genau diese Seite.
"""
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Nav-/Footer-Rauschen, das wie ein Linktext aussieht, aber keine Stelle ist.
RAUSCH_TEXT = {
    "home", "karriere", "career", "careers", "jobs", "stellen", "stellenangebote",
    "login", "anmelden", "suche", "search", "kontakt", "contact", "impressum",
    "datenschutz", "privacy", "cookie", "cookies", "accept", "akzeptieren",
    "weiter", "next", "zurück", "back", "mehr", "more", "alle anzeigen",
    "show all", "filter", "sortieren", "sort", "apply now", "jetzt bewerben",
    "share", "teilen", "print", "drucken", "newsletter", "über uns", "about us",
    "company website", "get in touch!", "get in touch", "clear search results",
    "current openings", "mehr erfahren", "spontanbewerbung", "initiativbewerbung",
    "read more", "learn more", "view all", "see all jobs", "all jobs", "all locations",
    "sign in", "sign up", "create account", "my account", "my profile", "talent community",
    "join talent community", "job alerts", "email me jobs", "save job", "saved jobs",
    "job coach",  # jobs.ch-Plattformfeature, steht auf jeder Firmenprofilseite
    "find a job", "join our team", "job openings", "job areas", "recruitment process",
    "top artikel", "various", "english", "deutsch", "français", "italiano",
    # Facetten/Kategorie-Filter, die wie Linktext aussehen, aber keine Stelle sind
    "students", "professionals", "graduates", "marketing & sales", "sales & marketing",
    "operations & production", "research & development", "project management",
    "it and software development", "sales and product service", "manufacturing",
    "engineering", "finance", "human resources", "supply chain", "quality",
}

# Nur der Zahlenteil ist variabel ("Jobs (20)", "See all 20 jobs") -> Regex statt Set.
RAUSCH_MUSTER = [
    re.compile(r"^jobs?\s*\(\d+\)$", re.I),
    re.compile(r"^see all\s*\d*\s*jobs?$", re.I),
]

# Card-Layouts, die Alter, Titel, Ort, Pensum etc. in EINEM <a>-Textblock
# zusammenkleben (Umantis, Workday-Renderings, viele Konzernseiten). Der
# eigentliche Titel steht meist zwischen einer optionalen Alters-Angabe am
# Anfang und dem ersten Feld-Label.
ALTER_PRAEFIX = re.compile(
    r"^(letzte[nr]?\s*(woche|monat)|vor\s*\d+\s*(tag(en)?|woche(n)?|monat(en)?|stunde(n)?)|"
    r"vorgestern|gestern|heute|"
    r"last\s*(week|month)|\d+\s*(days?|weeks?|months?|hours?)\s*ago|yesterday|today)\s*[:,-]?\s*",
    re.I,
)
FELD_LABEL = re.compile(
    r"\b(place of work|arbeitsort|workload|pensum|contract type|vertragsart|"
    r"anstellungsart|employment type)\s*:", re.I,
)
# "<Abteilung> Published: 24 Jan 2024 <Titel>, <Ort>" (Sandvik-Stil) -- hier
# steht der Titel NACH dem Label, nicht davor wie bei den anderen Feldern.
PUBLISHED = re.compile(r"published:\s*\d{1,2}\s+[a-zäöü]+\s+\d{4}\s*", re.I)

def titel_bereinigen(text):
    """Schneidet Alters-Praefix und alles ab dem ersten Feld-Label weg, falls
    eine Karte ihren ganzen Text (Titel+Ort+Pensum+...) in einen Link packt."""
    t = text
    m = PUBLISHED.search(t)
    if m:
        t = t[m.end():]
    t = ALTER_PRAEFIX.sub("", t, count=1).strip()
    m = FELD_LABEL.search(t)
    if m:
        t = t[:m.start()].strip(" -–*")
    return t

WORT = re.compile(r"[a-zA-ZäöüÄÖÜß]{2,}")

# Stellen-Detailseiten fast aller ATS-Systeme haben eine Job-ID/Slug im Pfad:
# ".../job/<titel>/<zahl>/", ".../jobs/<id>", ".../vacancy/12345" usw.
JOB_HREF = re.compile(
    r"(^|/)(job|jobs|stelle|stellen|vacature|vacatures|position|positions|"
    r"detail|vacancy|vacancies|opening|openings)(/|-|\?)",
    re.I,
)
# ".../job/<titel>/1234567/" (Tecan), ".../744000093298475-caldeireiro" (Smart-
# Recruiters), "...--4042993" (Rieter/Solique, doppelter Strich) -- die
# Job-ID kann nach "/" oder "-" stehen, optional gefolgt von einem Slug.
JOB_ID_ENDE = re.compile(r"[/-]\d{5,}(-[^/]*)?/?(\?.*)?$")

def _ist_rauschen(text):
    t = text.strip().lower()
    if t in RAUSCH_TEXT:
        return True
    if any(m.match(t) for m in RAUSCH_MUSTER):
        return True
    if len(t) < 6:
        return True
    # mind. zwei "Wörter", sonst meist ein Menüpunkt
    if len(WORT.findall(t)) < 2:
        return True
    return False

def _ist_job_href(href):
    return bool(JOB_HREF.search(href) or JOB_ID_ENDE.search(href))

def stellen_aus_html(html, basis_url, max_treffer=200, erlaube_generisch=False):
    """Gibt eine Liste von {"titel":.., "url":..} aus rohem HTML zurück.

    Nur Links, deren URL nach einer Job-Detailseite aussieht (Muster in
    JOB_HREF/JOB_ID_ENDE) -- das deckt die meisten ATS-Systeme praezise ab.
    Liefert das nichts, wird bewusst NICHT auf eine generische Link-Text-
    Heuristik zurueckgefallen: die fischt auf Marketing-/Konzernseiten (z.B.
    "Investor Relations", "Latest Insights") reihenweise Falschtreffer.
    Lieber ehrlich 0 Treffer ("Struktur nicht erkannt") als erfundene
    Stellen -- passend zur eigenen Projektregel "nie raten". Mit
    erlaube_generisch=True (z.B. fuer Playwright-gerenderte Einzelfaelle,
    wo der Aufrufer die Seite kennt) wird der Ruckfall trotzdem erlaubt."""
    soup = BeautifulSoup(html, "html.parser")

    def titel_aus_umgebung(a):
        """Manche Karten packen den Titel in eine Ueberschrift und lassen
        den Link nur 'Details'/'Mehr' sagen (z.B. Interroll). Dann in den
        umgebenden Containern (bis 5 Ebenen hoch) nach einer Ueberschrift
        suchen, die zur selben Karte gehoert."""
        knoten = a
        for _ in range(5):
            knoten = knoten.parent
            if knoten is None or knoten.name in ("body", "html"):
                break
            h = knoten.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            if h:
                t = h.get_text(" ", strip=True)
                if t:
                    return t
        return None

    TITEL_KLASSE = re.compile(r"job-?title|position-?title|vacancy-?title", re.I)

    def roh_titel(a):
        """Manche Karten packen Titel UND Abteilung/Pensum in denselben
        <a>-Textblock (SmartRecruiters: h4.job-title + p.job-desc). Dann
        lieber nur das spezifischere Titel-Element nehmen statt allem."""
        spezifisch = a.find(["h1", "h2", "h3", "h4", "h5", "h6"]) or \
                     a.find(class_=TITEL_KLASSE)
        if spezifisch:
            t = spezifisch.get_text(" ", strip=True)
            if t:
                return t
        return a.get_text(" ", strip=True)

    def sammeln(pruefung):
        treffer, gesehen = [], set()
        for a in soup.find_all("a", href=True):
            roh = roh_titel(a)
            href = a["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            if roh and len(roh) > 400:
                continue
            text = titel_bereinigen(roh) if roh else ""
            if (not text or _ist_rauschen(text)) and _ist_job_href(href):
                ersatz = titel_aus_umgebung(a)
                if ersatz:
                    text = titel_bereinigen(ersatz)
            if not text or len(text) < 4 or len(text) > 140:
                continue
            if not pruefung(text, href):
                continue
            url = urljoin(basis_url, href)
            key = (text.lower(), url)
            if key in gesehen:
                continue
            gesehen.add(key)
            treffer.append({"titel": text, "url": url})
            if len(treffer) >= max_treffer:
                break
        return treffer

    praezise = sammeln(lambda text, href: _ist_job_href(href) and not _ist_rauschen(text))
    if praezise or not erlaube_generisch:
        return praezise
    return sammeln(lambda text, href: not _ist_rauschen(text))
