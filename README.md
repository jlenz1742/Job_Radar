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
