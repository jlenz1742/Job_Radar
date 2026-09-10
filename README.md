# job-radar

Zustands- und Auswertungsmaschine für Jans Stellensuche in der Schweizer Industrie.

## Was das hier ist — und was nicht

Das Repo enthält den **deterministischen Teil**: Funde einlesen, Firma und Titel
normalisieren, gegen den Bestand deduplizieren, echte Neuzugänge markieren,
Excel bauen. Es enthält **keine Scraper**. Das Abrufen der Karriereseiten und
Alert-Mails passiert bislang durch den Agenten und wird als JSON übergeben.

Wer den Abruf nach GitHub Actions verlagern will, findet unter
`.github/workflows/` einen Entwurf — siehe Abschnitt „Actions" unten.

## Benutzung

```bash
python radar.py ingest lauf_2026-09-10.json   # Funde eines Laufs einlesen
python radar.py neu                            # Neuzugänge des letzten Laufs
python radar.py excel Job_Radar.xlsx           # Arbeitsmappe bauen
```

Zustand liegt in `state.json`. **Diese Datei ist das Gedächtnis** — wer sie
verliert, verliert die Unterscheidung zwischen „neu" und „kenne ich schon".
Deshalb gehört sie versioniert ins Repo: `git diff state.json` ist die
Veränderungsliste eines Laufs, kostenlos und mit voller Historie.

## Eingabeformat

```json
{
  "funde": [
    {"firma":"Tecan", "titel":"VP Commercial Operations EMEA",
     "ort":"Männedorf", "kanton":"ZH", "quelle":"Karriereseite",
     "quelle_id":"Tecan", "url":"https://…", "publiziert":"2026-09-08",
     "prio":"1", "teil":"1", "bewertung":"", "consulting":"", "notiz":""}
  ],
  "quellen": {"Tecan": 38, "Hilti": "FEHLER — job search unavailable"}
}
```

`quellen` ist Pflicht und trägt pro abgefragter Quelle entweder die Anzahl
gesehener Stellen (int) oder einen Fehlertext (string).

## Zwei Regeln, die teuer erkauft wurden

**1. „Weg" nur bei gesunder eigener Quelle.**
Eine Stelle darf nur dann als verschwunden gelten, wenn ihre eigene `quelle_id`
in diesem Lauf abgefragt wurde *und* sauber geliefert hat. Ohne diese Regel
erklärt ein Lauf, der nur fünf Quellen abdeckt, den gesamten Bestand für tot.
(Im Test: 48 Stellen fälschlich als weg markiert.)

**2. Eine Quelle mit plötzlich 0 Treffern ist verdächtig, nicht leer.**
Meldet eine Quelle 0, wo sie zuvor ≥5 hatte, wird Alarm ausgelöst *und* ihr
Urteil verworfen. Der gefährlichste Fehler des Radars ist die Quelle, die
antwortet aber nichts liefert — das sieht aus wie „keine neuen Stellen".
Real beobachtet bei Hilti (`job search is currently unavailable`).

## Dedup

Schlüssel ist `normalisierte_firma | normalisierter_titel`. Normalisierung
entfernt Umlaute, Rechtsformen (AG, GmbH, Group, Holding, Schweiz), Pensum-
angaben (`80-100%`), Gendersuffixe (`(m/w/d)`, `(a)`) und Satzzeichen.

Damit trifft ein LinkedIn-Alert-Eintrag
`Stadler Rail AG — Project Manager Strategic Projects 80-100%`
dieselbe Zeile wie der Karriereseiten-Fund
`Stadler Rail — Project Manager Strategic Projects`.

## jobs.ch — dokumentierte Fallstricke

| Problem | Umgehung |
|---|---|
| `&region=` → „Too many redirects" | Ort nach dem Abruf filtern |
| Suchbegriff mit 3+ Wörtern → Redirect-Fehler | Bindestriche: `Head-of-Sales` |
| `&sort=date` zerstört die Relevanz | nie verwenden |
| Seite 2 liefert unpassende Treffer | nur Seite 1 |
| `+` und `&` im Suchbegriff | durch `%20` ersetzen |
| Kurze Firmennamen: Rechtschreibkorrektur (`Gurit` → `guest`) | `?term=%22Gurit%22` |
| Viele Treffer sind Namensgleichheit | Firmennamen mit Zusatz präzisieren |

## Karriereseiten

38 der 52 Prio-1-Firmen liefern ihre Stellenliste serverseitig
(SuccessFactors, SmartRecruiters, Umantis, jobs.ch-Firmenprofile).
14 rendern nur per JavaScript (Workday, Eightfold) und brauchen einen
Headless-Browser. Kistler sperrt automatisierte Abrufe per robots.txt.

Etliche Konzernseiten paginieren clientseitig, akzeptieren aber einen
Länderfilter als URL-Parameter — bei Kistler funktionierte `?country=CH`.

## Actions

`.github/workflows/radar.yml` ist ein **Entwurf und ungetestet**. Er deckt nur
den Mail-Weg ab: Alert-Mails aus dem jobradar-Postfach per IMAP lesen, in das
Fundformat übersetzen, einlesen, Ergebnis committen.

Nötige Secrets:

- `IMAP_USER` — jan.jobradar@gmail.com
- `IMAP_PASS` — Google-App-Passwort

**Sicherheitshinweis:** Ein App-Passwort im Repo-Secret gewährt vollen Zugriff
auf dieses Postfach. Weil das jobradar-Konto ausschliesslich für diesen Zweck
existiert und keine private Korrespondenz enthält, ist das Risiko begrenzt —
aber es ist eine bewusste Entscheidung, keine Formalie. Niemals das Passwort
des privaten Kontos verwenden.

Der Mail-Parser (`parser/mail.py`) fehlt noch.

## abruf.py — der eigenständige Abruf (kein Agent nötig)

`radar.py` ruft bewusst nichts ab (siehe oben). `abruf.py` ist die Ergänzung
dazu: ein einziges Kommando, das Karriereseiten und jobs.ch wirklich abfragt,
die Treffer normalisiert und direkt in `radar.py` einspeist:

```bash
pip install -r requirements.txt
python abruf.py run --prio 1              # Prio-1-Firmen, alles
python abruf.py run --prio 1,2 --pause 1   # mehrere Priostufen, hoeflicher
python abruf.py run --prio 1 --kein-js     # Karriereseiten ohne Playwright
                                            # (Workday/Eightfold ueberspringen,
                                            # nur noch jobs.ch fuer die 14 Firmen)
```

Am Ende steht `Job_Radar.xlsx` auf dem neuesten Stand, `state.json` hat den
Lauf verbucht, und `laeufe/lauf_<datum>_<zeit>.json` haelt die Rohtreffer
dieses Laufs fest (Fund- und Quellenformat wie gewohnt).

**Bausteine** (`fetch/`):
- `static_page.py` — Karriereseiten, die serverseitig rendern (`requests`)
- `js_page.py` — Karriereseiten, die nur per JavaScript rendern (Workday,
  Eightfold, ...) via Playwright/Headless-Chromium
- `jobsch.py` — jobs.ch-Stichwortsuche, nach echtem Arbeitgeber gefiltert
- `extract.py` — die Heuristik, die aus HTML Job-Titel+Link herausliest

**Die Heuristik ist generisch, kein Parser pro ATS-System.** Sie erkennt
Job-Detailseiten am URL-Muster (`.../job/<titel>/<id>/` o.ä.) — das deckt die
meisten Konzern-Karriereseiten ab. Erkennt sie nichts, liefert sie bewusst
**0 Treffer statt zu raten** (`FEHLER — Struktur nicht erkannt`): lieber eine
sichtbare Lücke als erfundene Stellen aus der Marketing-Navigation.
Betroffene Firmen brauchen einen eigenen Blick auf ihre Seite.

**Wichtiger Fallstrick, live gegengeprüft:** jobs.ch liefert einem Client mit
Browser-User-Agent (aber ohne echtes JS dahinter) einen Satz Köder-Treffer
statt der echten Suche. `fetch/jobsch.py` verzichtet deshalb absichtlich auf
einen Browser-UA.

**Priorisierung ändern:** Nur `daten/Zielliste_CH_Industrie.xlsx`, Spalte
`Prio`, editieren — dann `python tools/sync_quellen.py` laufen lassen. Das
baut `daten/quellen.json` komplett neu; nichts davon von Hand editieren.

**Bekannte Lücke — Playwright/HTTPS in Sandboxen mit erzwungenem Proxy:**
In einer Umgebung, die ausgehendes HTTPS zwingend über einen eigenen
TLS-re-terminierenden Proxy leitet (wie die Cloud-Sandbox, in der dieses
Tool entwickelt wurde), scheitert Headless-Chromium beim CONNECT-Handshake
(`ERR_CONNECTION_RESET`, selbst zu example.com) — plain HTTP über denselben
Proxy funktioniert einwandfrei. `curl`/`requests` sind nicht betroffen. Der
JS-Pfad (`--kein-js` weglassen) ist deshalb nur auf einem normalen Rechner
oder in GitHub Actions getestet, nicht in dieser Sandbox. Falls es doch mal
dort laufen soll: zuerst `curl -x $HTTPS_PROXY https://example.com` pruefen.

**Vor dem ersten echten Lauf mit JS-Firmen** (also ohne `--kein-js`) einmal
pruefen, dass Playwright bei dir wirklich durchkommt:

```bash
playwright install chromium
python tools/test_js_lokal.py
```

Testet 4 der 15 JS-only-Firmen (Workday + Eightfold) und sagt ehrlich, ob es
am Mechanismus oder an der einzelnen Seite liegt, falls etwas schiefgeht.
