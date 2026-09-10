# -*- coding: utf-8 -*-
"""
bericht.py — tägliche Zusammenfassung: neue Jobs der letzten 5 Tage
(Übersicht) + eine mit der Claude API bewertete Shortlist der
vielversprechendsten, veröffentlicht als GitHub Issue.

**Kein Keyword-Raster.** Jan will keine Stelle durch einen starren
Titel-Filter verlieren, den ein Python-Skript nie so nuanciert lesen kann
wie eine Anzeige es verlangt -- deshalb sieht die Claude API JEDEN neuen
Job aus der Übersicht und entscheidet selbst, was STARK/MÖGLICH ist. Die
Shortlist hat KEINE feste Obergrenze -- so viele Treffer wie tatsächlich
gut sind, nie künstlich auf eine Zahl gestutzt, aber auch nie aufgefüllt,
wenn nichts passt. `SICHERHEITSDECKEL` ist keine Auswahl-Grenze, sondern
nur ein Schutz gegen einen entgleisten Lauf (siehe dort).

Die Übersicht ist UNGEFILTERT (alle neuen Jobs, letzte 5 Tage). Ein Fehler
bei der Shortlist (kein Secret, API nicht erreichbar) lässt die Übersicht
trotzdem als Issue raus, nur ohne Shortlist-Abschnitt -- kein Grund, den
ganzen Bericht zu unterschlagen.

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

TAGE_UEBERSICHT = 5
CLAUDE_MODELL = "claude-sonnet-5"
# NUR ein Schutz gegen Kosten/Kontext-Explosion an einem entgleisten Tag
# (z.B. ein Erstlauf mit hunderten "neuen" Jobs). Im Normalbetrieb (ein
# paar neue Jobs pro Tag) greift das nie. Wenn es doch greift, wird das
# im Issue UND im Log sichtbar gemacht -- niemals stillschweigend
# Kandidaten verschwinden lassen.
SICHERHEITSDECKEL = 250

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

def kandidaten_fuer_api(jobs, deckel=SICHERHEITSDECKEL):
    """Normalerweise identisch mit `jobs` -- nur an einem entgleisten Tag
    (siehe SICHERHEITSDECKEL) wird tatsaechlich gekuerzt, und dann nach
    Geografie/Zielfirmen-Zugehoerigkeit sortiert, damit die wahrschein-
    licheren Treffer im gekuerzten Teil erhalten bleiben."""
    if len(jobs) <= deckel:
        return jobs, 0
    sortiert = sorted(jobs, key=lambda j: (radius(j.get("kanton")) == "drin",
                                            j.get("teil") == "1"), reverse=True)
    return sortiert[:deckel], len(jobs) - deckel

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
        f"Hier ist die VOLLSTAENDIGE Liste der neuen Stellenanzeigen der letzten "
        f"{TAGE_UEBERSICHT} Tage (nur Titel/Firma/Ort, keine Volltexte). Geh jede "
        f"einzeln durch und waehle ALLE aus, die fuer Jan wirklich vielversprechend "
        f"sind (STARK oder starkes MOEGLICH) -- keine feste Anzahl, keine Obergrenze. "
        f"Sind es 2, gib 2 zurueck. Sind es 20 echte Treffer, gib 20 zurueck. "
        f"Niemals auffuellen, wenn weniger passen, und keine Stelle uebergehen, "
        f"die inhaltlich passt, nur weil der Titel ungewoehnlich formuliert ist. "
        f"Fuer jede gewaehlte Stelle: Einstufung (STARK/MOEGLICH) und ein bis zwei "
        f"Saetze Begruendung, warum sie passt und was auffaellt -- ehrlich, nicht "
        f"beschoenigend, wie in den Projektregeln oben beschrieben.\n\n"
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
                # Grosszuegig, weil die Shortlist keine Obergrenze hat --
                # bei vielen echten Treffern darf die Antwort entsprechend lang sein.
                "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
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

def issue_markdown(uebersicht, shortlist, shortlist_fehler, uebersprungen=0):
    heute = date.today().isoformat()
    teile = [f"{len(uebersicht)} neue Stellen in den letzten {TAGE_UEBERSICHT} Tagen.\n"]
    if uebersprungen:
        teile.append(
            f"\n> ⚠️ SICHERHEITSDECKEL gegriffen: {uebersprungen} Stellen wurden der "
            f"Shortlist-Bewertung NICHT vorgelegt (siehe `tools/bericht.py`). "
            f"Das ist ein Anzeichen fuer einen entgleisten Lauf, nicht der "
            f"Normalfall -- bitte nachschauen.\n"
        )

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
    kandidaten, uebersprungen = kandidaten_fuer_api(uebersicht)
    if uebersprungen:
        print(f"WARNUNG: SICHERHEITSDECKEL gegriffen, {uebersprungen} Stellen "
              f"nicht an die Shortlist-Bewertung uebergeben.")
    shortlist, fehler = claude_shortlist(kandidaten)
    print(f"{len(uebersicht)} neue Jobs, {len(kandidaten)} der Shortlist-Bewertung vorgelegt, "
          f"{len(shortlist) if shortlist else 0} in der Shortlist"
          + (f" (Fehler: {fehler})" if fehler else ""))

    body = issue_markdown(uebersicht, shortlist or [], fehler, uebersprungen)
    titel = f"Job-Radar — {date.today().isoformat()}"
    issue_erstellen(titel, body)

if __name__ == "__main__":
    main()
