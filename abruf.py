# -*- coding: utf-8 -*-
"""
abruf.py — die "Hände" des Job-Radars: ruft die Quellen wirklich ab.

Im Unterschied zu radar.py (rein deterministisch, ruft nichts ab) macht
dieses Skript den kompletten Lauf in einem Kommando:

    python abruf.py run [--prio 1] [--js aus]

1. liest daten/quellen.json (Prioliste, per tools/sync_quellen.py aus der
   Zielliste-Excel gebaut)
2. ruft fuer jede Firma der gewaehlten Prio(s) ab:
     - Karriereseite: statisch (requests) oder, wenn typ=js_only, per
       Playwright gerendert
     - jobs.ch-Stichwortsuche (immer zusaetzlich, deckt auch Firmen ohne
       bekannte Karriereseite ab)
3. schreibt lauf_<datum>.json im Fundformat von radar.py
4. ruft radar.ingest() und radar.excel() direkt auf

Eine kaputte oder blockierte Quelle bricht den Lauf NICHT ab -- sie wird als
FEHLER im quellen-Status vermerkt (radar.py behandelt das: eine Stelle gilt
nur dann als "weg", wenn ihre Quelle in diesem Lauf gesund geliefert hat).
"""
import argparse, json, os, sys, time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import radar
from fetch.static_page import fetch_static
from fetch.jobsch import fetch_jobsch

# Grobe Ort-Text -> Kanton-Kuerzel-Abbildung fuer jobs.ch-Treffer
# ("Baden, Aargau, Switzerland" -> "AG"). Career-Page-Treffer haben meist
# keinen Ort pro Stelle -- dort wird der HQ-Kanton der Firma aus der
# Zielliste als Naeherung verwendet.
KANTON_NAMEN = {
    "zuerich": "ZH", "zürich": "ZH", "aargau": "AG", "bern": "BE", "berne": "BE",
    "luzern": "LU", "uri": "UR", "schwyz": "SZ", "obwalden": "OW", "nidwalden": "NW",
    "glarus": "GL", "zug": "ZG", "freiburg": "FR", "fribourg": "FR", "solothurn": "SO",
    "basel-stadt": "BS", "basel-landschaft": "BL", "schaffhausen": "SH",
    "appenzell ausserrhoden": "AR", "appenzell innerrhoden": "AI", "st. gallen": "SG",
    "st gallen": "SG", "graubuenden": "GR", "graubünden": "GR", "grisons": "GR",
    "thurgau": "TG", "tessin": "TI", "ticino": "TI", "waadt": "VD", "vaud": "VD",
    "wallis": "VS", "valais": "VS", "neuenburg": "NE", "neuchatel": "NE",
    "neuchâtel": "NE", "genf": "GE", "geneve": "GE", "genève": "GE", "geneva": "GE",
    "jura": "JU",
}

def kanton_aus_ort(ort_text, default=""):
    if not ort_text:
        return default
    teile = [t.strip().lower() for t in ort_text.split(",")]
    for t in teile:
        if t in KANTON_NAMEN:
            return KANTON_NAMEN[t]
    return default

def abruf_karriereseite(quelle):
    firma = quelle["firma"]
    typ = quelle["typ"]
    if typ == "abrufbar" and quelle.get("karriereseite"):
        stellen, err = fetch_static(quelle["karriereseite"])
        return stellen, err
    if typ == "js_only" and quelle.get("karriereseite"):
        try:
            from fetch.js_page import fetch_js
            stellen, err = fetch_js(quelle["karriereseite"])
        except Exception as e:
            stellen, err = [], f"FEHLER — Playwright: {type(e).__name__}: {e}"[:150]
        return stellen, err
    return [], None  # kein bekannter Weg -> stumm auslassen, nicht als Fehler werten

def firma_zu_funde(firma, stellen, quelle_id, quelle_name, prio, default_kanton, default_ort):
    out = []
    for s in stellen:
        ort = s.get("ort") or default_ort
        kanton = kanton_aus_ort(ort, default_kanton)
        out.append({
            "firma": s.get("firma_jobsch") or firma,
            "titel": s["titel"],
            "ort": ort,
            "kanton": kanton,
            "quelle": quelle_name,
            "quelle_id": quelle_id,
            "url": s["url"],
            "publiziert": "",
            "prio": prio,
            "teil": "1",
            "bewertung": "", "consulting": "", "notiz": "",
        })
    return out

def run(prios, mit_jobsch, mit_js, pause):
    with open(os.path.join(HERE, "daten", "quellen.json"), encoding="utf-8") as f:
        quellen = json.load(f)["quellen"]
    ziel = [q for q in quellen if q["prio"] in prios]

    funde, quellen_status = [], {}
    print(f"{len(ziel)} Firmen fuer Prio {sorted(prios)}")

    for i, q in enumerate(ziel, 1):
        firma = q["firma"]
        print(f"[{i}/{len(ziel)}] {firma} ({q['typ']})", end=" ", flush=True)

        n_vorher = len(funde)
        if q["typ"] in ("abrufbar", "js_only") and (mit_js or q["typ"] == "abrufbar"):
            stellen, err = abruf_karriereseite(q)
            qid = f"{firma} (Karriereseite)"
            if err:
                quellen_status[qid] = err
            elif stellen:
                quellen_status[qid] = len(stellen)
                funde.extend(firma_zu_funde(firma, stellen, firma, "Karriereseite",
                                             q["prio"], q["kanton"], q["ort"]))

        if mit_jobsch:
            stellen, err = fetch_jobsch(firma, q.get("jobs_ch_suchbegriff"))
            qid = f"{firma} (jobs.ch)"
            if err:
                quellen_status[qid] = err
            else:
                quellen_status[qid] = len(stellen)
                funde.extend(firma_zu_funde(firma, stellen, firma, "jobs.ch",
                                             q["prio"], q["kanton"], q["ort"]))

        print(f"-> {len(funde) - n_vorher} Treffer")
        if pause:
            time.sleep(pause)

    # Eigener Ordner statt lauf_<datum>.json im Root: dort liegt bereits
    # lauf_2026-09-10.json als kuratiertes Dry-Run-Beispiel aus der
    # Uebergabe -- automatische Laeufe sollen das nie ueberschreiben.
    os.makedirs(os.path.join(HERE, "laeufe"), exist_ok=True)
    heute = date.today().isoformat()
    uhrzeit = time.strftime("%H%M%S")
    lauf_pfad = os.path.join(HERE, "laeufe", f"lauf_{heute}_{uhrzeit}.json")
    with open(lauf_pfad, "w", encoding="utf-8") as f:
        json.dump({"funde": funde, "quellen": quellen_status}, f, ensure_ascii=False, indent=1)
    print(f"\n{lauf_pfad} geschrieben | {len(funde)} Rohtreffer | {len(quellen_status)} Quellen")

    radar.ingest(lauf_pfad)
    radar.excel(os.path.join(HERE, "Job_Radar.xlsx"))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--prio", default="1", help="Kommagetrennt, z.B. 1,2")
    ap.add_argument("--kein-jobsch", action="store_true")
    ap.add_argument("--kein-js", action="store_true",
                     help="JS-only-Karriereseiten (Playwright) ueberspringen")
    ap.add_argument("--pause", type=float, default=0.5,
                     help="Sekunden Pause zwischen Firmen (Hoeflichkeit ggue. den Servern)")
    args = ap.parse_args()
    run(set(args.prio.split(",")), not args.kein_jobsch, not args.kein_js, args.pause)
