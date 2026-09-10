# -*- coding: utf-8 -*-
"""
bericht.py — tägliche Zusammenfassung: neue Jobs der letzten 3 Tage
(Übersicht) + eine mit der Claude API bewertete Shortlist der
vielversprechendsten, veröffentlicht als GitHub Issue.

Zwei Stufen, um Kosten und Rauschen klein zu halten:
1. Regel-Vorfilter (Python, kostenlos): Rollen-Keywords und Ausschlüsse
   aus CLAUDE.md, reduziert auf höchstens VORFILTER_CAP Kandidaten.
2. Die Claude API bewertet genau diese Kandidaten inhaltlich
   (STARK/MÖGLICH + Begründung) und wählt die Top SHORTLIST_GROESSE aus.

Die Übersicht ist UNGEFILTERT (alle neuen Jobs) -- nur die Shortlist geht
durch den Vorfilter + die API. Ein Fehler in Schritt 2 (kein Secret, API
nicht erreichbar) lässt die Übersicht trotzdem als Issue raus, nur ohne
Shortlist-Abschnitt -- kein Grund, den ganzen Bericht zu unterschlagen.

Aufruf:  python tools/bericht.py
Env:     ANTHROPIC_API_KEY, GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo,
         in GitHub Actions automatisch gesetzt über ${{ github.repository }})
"""
import json, os, re, sys
from datetime import date, timedelta
import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from radar import radius

TAGE_UEBERSICHT = 3
VORFILTER_CAP = 40
SHORTLIST_GROESSE = 8
CLAUDE_MODELL = "claude-sonnet-5"

# Aus CLAUDE.md "Relevante Rollen" / "Nicht relevant" -- bei Aenderung dort
# auch hier nachziehen. Bewusst keine automatische Extraktion aus dem
# Prosa-Text, damit eine Formulierungsaenderung dort nicht lautlos den
# Filter verstellt.
ROLLEN_KEYWORDS = [
    "business development", "head of sales", "vertriebsleiter", "commercial director",
    "commercial excellence", "go-to-market", "go to market", "pricing",
    "key account", "corporate development", "strategie", "head of strategy",
    "strategieprojekt", "referent der geschäftsleitung", "m&a", "mergers",
    "post merger", "post-merger", "transformation", "marketing-leitung",
    "marketing leitung", "head of marketing", "product management", "product manager",
    "sales director", "sales manager", "vertriebsleitung", "commercial",
]
NICHT_RELEVANT_KEYWORDS = [
    "sachbearbeiter", "praktikant", "praktikum", "lehrstelle", "lehre als",
    "trainee", "werkstudent", "servicetechniker", "einkäufer", "einkauf",
    "qualitätsprüfer", "personalsachbearbeiter", "buchhalter",
    "produktionsmitarbeiter", "montagemitarbeiter", "logistiker", "lagerist",
    "elektroniker", "mechaniker", "monteur", "operator", "schichtleiter",
    "ausbildung", "apprenti", "lehrling",
]

def _vor_n_tagen(datum_str, tage):
    try:
        d = date.fromisoformat(datum_str)
    except (ValueError, TypeError):
        return False
    return d >= date.today() - timedelta(days=tage)

def neue_jobs(state, tage=TAGE_UEBERSICHT):
    jobs = [j for j in state["jobs"].values()
            if j.get("status") != "weg" and _vor_n_tagen(j.get("erstmals"), tage)]
    jobs.sort(key=lambda j: (j.get("erstmals", ""), j.get("firma", "")), reverse=True)
    return jobs

def ist_rollen_relevant(titel):
    t = (titel or "").lower()
    if any(k in t for k in NICHT_RELEVANT_KEYWORDS):
        return False
    return any(k in t for k in ROLLEN_KEYWORDS)

def vorfiltern(jobs, cap=VORFILTER_CAP):
    kandidaten = [j for j in jobs if ist_rollen_relevant(j.get("titel", ""))]
    kandidaten.sort(key=lambda j: (radius(j.get("kanton")) == "drin",
                                    j.get("teil") == "1"), reverse=True)
    return kandidaten[:cap]

def profil_text():
    """Nur der fachliche Teil von CLAUDE.md (Profil/Kriterien), nicht die
    technischen Abschnitte weiter unten -- die brauchen wir hier nicht."""
    try:
        with open(os.path.join(HERE, "CLAUDE.md"), encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return ""
    ende = text.find("## Aufbau")
    return text[:ende] if ende > 0 else text[:4000]

def claude_shortlist(kandidaten):
    """Gibt (shortlist, fehler) zurueck -- genau eines von beiden ist gesetzt."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "ANTHROPIC_API_KEY nicht gesetzt"
    if not kandidaten:
        return [], None

    liste = "\n".join(
        f"{i + 1}. {j.get('firma', '')} — {j.get('titel', '')} "
        f"({j.get('ort', '')}, {j.get('kanton', '')})  URL: {j.get('url', '')}"
        for i, j in enumerate(kandidaten)
    )
    prompt = (
        f"{profil_text()}\n\n"
        f"Hier ist eine Liste neuer Stellenanzeigen (nur Titel/Firma/Ort, keine "
        f"Volltexte). Waehle daraus die bis zu {SHORTLIST_GROESSE} vielversprechendsten "
        f"fuer Jan aus -- nur wirklich gute Kandidaten (STARK oder starkes MOEGLICH), "
        f"niemals auffuellen, wenn weniger passen. Fuer jede gewaehlte Stelle: "
        f"Einstufung (STARK/MOEGLICH) und ein bis zwei Saetze Begruendung, warum sie "
        f"passt und was auffaellt -- ehrlich, nicht beschoenigend, wie in den "
        f"Projektregeln oben beschrieben.\n\n"
        f"Stellen:\n{liste}\n\n"
        f'Antworte NUR mit JSON, keine Erklaerung davor oder danach: '
        f'{{"shortlist": [{{"nr": 1, "einstufung": "STARK", "begruendung": "..."}}]}}\n'
        f'"nr" bezieht sich auf die Nummer in der Liste oben.'
    )

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODELL,
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=90,
        )
        r.raise_for_status()
        antwort = r.json()["content"][0]["text"].strip()
        antwort = re.sub(r"^```(json)?|```$", "", antwort, flags=re.MULTILINE).strip()
        daten = json.loads(antwort)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:200]

    ergebnis = []
    for eintrag in daten.get("shortlist", []):
        try:
            job = kandidaten[int(eintrag["nr"]) - 1]
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        ergebnis.append({**job, "einstufung": eintrag.get("einstufung", ""),
                          "begruendung": eintrag.get("begruendung", "")})
    return ergebnis, None

def issue_markdown(uebersicht, shortlist, shortlist_fehler):
    heute = date.today().isoformat()
    teile = [f"{len(uebersicht)} neue Stellen in den letzten {TAGE_UEBERSICHT} Tagen.\n"]

    teile.append("\n## Shortlist\n")
    if shortlist_fehler:
        teile.append(f"\n> ⚠️ Shortlist nicht verfügbar: {shortlist_fehler}\n")
    elif not shortlist:
        teile.append("\nKeine Stelle war stark genug für die Shortlist.\n")
    else:
        for j in shortlist:
            teile.append(
                f"\n- **[{j.get('einstufung', '')}]** "
                f"[{j.get('titel', '')}]({j.get('url', '')})"
                f" — {j.get('firma', '')}, {j.get('ort', '')}"
                f"\n  {j.get('begruendung', '')}\n"
            )

    teile.append("\n## Übersicht — alle neuen Stellen\n")
    if not uebersicht:
        teile.append("\nKeine neuen Stellen in diesem Zeitraum.\n")
    else:
        aktueller_tag = None
        for j in uebersicht:
            tag = j.get("erstmals", "")
            if tag != aktueller_tag:
                teile.append(f"\n### {tag}\n")
                aktueller_tag = tag
            teile.append(
                f"- {j.get('firma', '')} — "
                f"[{j.get('titel', '')}]({j.get('url', '')}) ({j.get('ort', '')})\n"
            )
    return "".join(teile)

def issue_erstellen(titel, body):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN/GITHUB_REPOSITORY nicht gesetzt -- kein Issue angelegt.\n")
        print(body)
        return
    r = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"title": titel, "body": body},
        timeout=30,
    )
    if r.status_code >= 300:
        print(f"Issue konnte nicht angelegt werden: HTTP {r.status_code} {r.text[:300]}")
    else:
        print(f"Issue angelegt: {r.json().get('html_url')}")

def main():
    with open(os.path.join(HERE, "state.json"), encoding="utf-8") as f:
        state = json.load(f)

    uebersicht = neue_jobs(state)
    kandidaten = vorfiltern(uebersicht)
    shortlist, fehler = claude_shortlist(kandidaten)
    print(f"{len(uebersicht)} neue Jobs, {len(kandidaten)} Kandidaten vorgefiltert, "
          f"{len(shortlist) if shortlist else 0} in der Shortlist"
          + (f" (Fehler: {fehler})" if fehler else ""))

    body = issue_markdown(uebersicht, shortlist or [], fehler)
    titel = f"Job-Radar — {date.today().isoformat()}"
    issue_erstellen(titel, body)

if __name__ == "__main__":
    main()
