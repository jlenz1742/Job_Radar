# -*- coding: utf-8 -*-
"""
sync_quellen.py — baut daten/quellen.json aus Zielliste_CH_Industrie.xlsx.

Die Excel (Blatt "Zielliste") ist die einzige Wahrheit für Priorisierung.
Wer eine Firma hoch- oder herunterstufen will, ändert nur die Spalte "Prio"
in der Excel und lässt dieses Skript laufen — quellen.json wird komplett
neu geschrieben, nie händisch editiert.

Aufruf:
    python tools/sync_quellen.py [Zielliste_CH_Industrie.xlsx] [daten/quellen.json]
"""
import json, os, sys
import openpyxl

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPALTEN = {
    "nr": 0, "prio": 1, "firma": 2, "ort": 3, "kanton": 4, "segment": 5,
    "jobs_ch_suchbegriff": 22, "karriereseite": 24,
}

def typ_und_url_und_hinweis(karriereseite):
    """Leitet typ/url/hinweis aus der freien Textspalte 'Karriereseite (geprüft)'
    ab. Drei Formen sind erlaubt:
      "https://..."                                -> abrufbar, url, ""
      "https://... — nicht abrufbar ohne Rendern"   -> js_only, url, hinweis
      "nicht abrufbar — <grund>"                    -> js_only, "", hinweis
      "" / leer                                     -> ungeprueft, "", ""
    """
    s = (karriereseite or "").strip()
    if not s:
        return "ungeprueft", "", ""
    if s.lower().startswith("http"):
        if "—" in s:
            url, rest = s.split("—", 1)
            return "js_only", url.strip(), rest.strip()
        return "abrufbar", s, ""
    if s.lower().startswith("nicht abrufbar"):
        hinweis = s.split("—", 1)[1].strip() if "—" in s else s
        return "js_only", "", hinweis
    return "ungeprueft", "", s

def main(xlsx_pfad, out_pfad):
    wb = openpyxl.load_workbook(xlsx_pfad, data_only=True)
    ws = wb["Zielliste"]
    rows = list(ws.iter_rows(values_only=True))[1:]  # Header weg

    quellen = []
    for r in rows:
        if r[SPALTEN["firma"]] is None:
            continue
        karriereseite = r[SPALTEN["karriereseite"]]
        typ, url, hinweis = typ_und_url_und_hinweis(karriereseite)
        eintrag = {
            "nr": r[SPALTEN["nr"]],
            "prio": str(r[SPALTEN["prio"]]),
            "firma": r[SPALTEN["firma"]],
            "ort": r[SPALTEN["ort"]],
            "kanton": r[SPALTEN["kanton"]],
            "segment": r[SPALTEN["segment"]],
            "jobs_ch_suchbegriff": r[SPALTEN["jobs_ch_suchbegriff"]] or r[SPALTEN["firma"]],
            "karriereseite": url,
            "typ": typ,
            "hinweis": hinweis,
        }
        quellen.append(eintrag)

    out = {
        "stand": __import__("datetime").date.today().isoformat(),
        "quellen": quellen,
    }
    with open(out_pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    from collections import Counter
    print(f"{out_pfad} geschrieben | {len(quellen)} Firmen total")
    print("nach Prio:", dict(Counter(q["prio"] for q in quellen)))
    print("nach Typ: ", dict(Counter(q["typ"] for q in quellen)))

if __name__ == "__main__":
    xlsx = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "daten", "Zielliste_CH_Industrie.xlsx")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "daten", "quellen.json")
    main(xlsx, out)
