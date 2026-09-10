# job-radar — Projektanweisungen

Jan sucht eine Stelle in der Schweizer Industrie und will aus der Beratung raus.
Dieses Repo ist sein Job-Radar: es findet neue Stellen, merkt sich was er schon
gesehen hat, und zeigt nur die Differenz.

## Kandidatenprofil

Jan, Project Leader bei Roland Berger, sechs Jahre Commercial Strategy
(Pricing, Go-to-Market, Vertriebsorganisation, Key Account Management),
davor Simon-Kucher, davor Sensirion (M&A nach dem IPO, Produktionsprozesse).
ETH-Maschinenbau. Wohnt in Meilen am Zürichsee.

**Die harte Wahrheit über seine Bewerbungen:** Von 20 im Dry Run geprüften
Inseraten verlangte genau eines ausdrücklich Beratungserfahrung. Fast alle
anderen fordern entweder eine Linienlaufbahn (geführte Vertriebsorganisation,
eigenes P&L, selbst erschlossene Märkte) oder enge Domänenerfahrung.
Sein ETH-Abschluss räumt technische Ausbildungshürden aus dem Weg; die Hürde,
an der es scheitert, ist fast immer die fehlende eigene Umsatz- und
Führungsverantwortung im Investitionsgütervertrieb.

Bewerte Stellen entsprechend **ehrlich**. Beschönige keinen Fit. Wenn ein
Inserat eine technische Grundausbildung, Branchenerfahrung oder Verkaufs-
erfahrung verlangt, die er nicht hat, sag das deutlich. Einstufung:
STARK / MÖGLICH / SCHWACH.

## Relevante Rollen

Business Development · Head of Sales / Vertriebsleiter / Commercial Director ·
Commercial Excellence · Go-to-Market · Pricing · Key Account Management
(Leitungsebene) · Corporate Development · Strategie / Head of Strategy /
Strategieprojekte / Referent der Geschäftsleitung · M&A · Post Merger
Integration · Transformation · Marketing-Leitung · Product Management auf
Leitungsebene.

Nicht relevant: Sachbearbeiter, Praktika, Lehrstellen, Trainee, Werkstudent,
reine IT-/Software-Rollen, reine Ingenieurs- und Produktionsrollen,
Servicetechniker, Einkauf, Finanzen, HR, Qualität.

Stellen, die Beratungserfahrung ausdrücklich verlangen, **markieren** —
das sind seine besten Chancen.

## Geografie

Der Radius von rund 100 km um Zürich wird als Kantonsliste umgesetzt, nicht
als Distanzrechnung, weil Inserate den Ort oft nur grob angeben.

**Drin:** ZH ZG SZ AG SH TG SG AR AI LU NW OW UR GL BL BS SO BE und Liechtenstein
**Draussen:** GE VD VS NE JU FR TI GR
Nur „Schweiz" oder „Deutschschweiz" ohne Ort zählt als drin.

Der Radius gilt für **Teil 2** (Empfehlungen aus dem breiteren Markt).
Treffer bei den Zielfirmen werden unabhängig vom Ort gezeigt, aber als
„weiter weg" markiert.

## Aufbau

**Teil 1 — Zielfirmen.** 38 geprüfte Karriereseiten der Prio-1-Firmen
täglich; die 14 JavaScript-only-Firmen und die 38 Prio-2-Firmen über
jobs.ch. Quellen stehen maschinenlesbar in `daten/quellen.json`.

**Teil 2 — Empfehlungen.** Stichwortsuchen bei Firmen, die *nicht* auf der
Zielliste stehen, innerhalb des Radius. Das ist der Teil, der die Liste
erweitert statt sie nur abzufragen.

## Regeln, die nicht verhandelbar sind

1. **Das jobradar-Postfach wird nur gelesen.** Nichts löschen, nichts
   archivieren, nichts als gelesen markieren.
2. **Kein LinkedIn- oder Indeed-Scraping.** Die Alert-Mails auszulesen ist in
   Ordnung, das Portal zu scrapen nicht.
3. **Nie raten.** Eine Quelle, die nicht abrufbar ist, heisst „nicht
   abrufbar" — niemals Inhalte erfinden oder aus dem Firmennamen ableiten.
4. **Stille Ausfälle sichtbar machen.** Eine Quelle, die antwortet aber
   nichts liefert, sieht aus wie „keine neuen Stellen" und ist der
   gefährlichste Fehler des ganzen Systems. Real beobachtet bei Hilti.

## Zwei Regeln im Code, die teuer erkauft wurden

**„Weg" nur bei gesunder eigener Quelle.** Eine Stelle darf nur dann als
verschwunden gelten, wenn ihre `quelle_id` in diesem Lauf abgefragt wurde
*und* sauber geliefert hat. Ohne diese Regel erklärt ein Lauf, der nur fünf
Quellen abdeckt, den ganzen Bestand für tot (im Test: 48 Stellen).

**Eine Quelle mit plötzlich 0 Treffern ist verdächtig, nicht leer.** Meldet
sie 0, wo sie zuvor ≥5 hatte, wird Alarm ausgelöst *und* ihr Urteil verworfen.

Beide Regeln nicht ohne Not anfassen.

## jobs.ch — Fallstricke

| Problem | Umgehung |
|---|---|
| `&region=` → „Too many redirects" | Ort nach dem Abruf filtern |
| Suchbegriff mit 3+ Wörtern → Redirect-Fehler | Bindestriche: `Head-of-Sales` |
| `&sort=date` zerstört die Relevanz | nie verwenden |
| Seite 2 liefert unpassende Treffer | nur Seite 1 |
| `+` und `&` im Suchbegriff | durch `%20` ersetzen |
| Kurze Firmennamen → Rechtschreibkorrektur (`Gurit`→`guest`) | `?term=%22Gurit%22` |
| Viele Treffer sind blosse Namensgleichheit | Firmennamen präzisieren |

## Karriereseiten

38 der 52 Prio-1-Firmen liefern serverseitig (SuccessFactors, SmartRecruiters,
Umantis, jobs.ch-Firmenprofile). 14 rendern nur per JavaScript (Workday,
Eightfold) und brauchen einen Headless-Browser. Kistler sperrt automatisierte
Abrufe per robots.txt.

Viele Konzernseiten paginieren clientseitig, akzeptieren aber einen
Länderfilter als URL-Parameter — bei Kistler funktionierte `?country=CH`.

Bekannt kaputt: **Hilti** („job search is currently unavailable"),
**Sandvik** (Länderfilter nicht ansteuerbar), **Haag-Streit** (11 von 20
Stellen nur per JS), **Liebherr** (nur 10 von 66 CH-Stellen abrufbar),
**ABB** (Trefferzahl schwankt zwischen 16 und 93).

Gar nicht auf jobs.ch: Gurit, Zünd, INFICON, Everllence, Ascom.

## Postfach

`jan.jobradar@gmail.com`. Relevante Absender:

- `jobmail@jobs.ch` — Job-Alarm, ein Mail pro Abo
- `jobalerts-noreply@linkedin.com` — Jobbenachrichtigung
- `jobs-noreply@linkedin.com` — „ähnliche Jobs wie …"

Rauschen, ignorieren: `newsletters-noreply@linkedin.com`,
`willkommen@my.jobs.ch`, `no_reply@jobs.ch`.

## Ablauf eines Laufs

```bash
python radar.py ingest lauf.json    # Funde einlesen, Differenz bilden
python radar.py neu                 # Neuzugänge auflisten
python radar.py excel Job_Radar.xlsx
```

`state.json` ist das Gedächtnis und gehört versioniert ins Repo.
`git diff state.json` ist damit die Veränderungsliste eines Laufs — mit
voller Historie und ohne dass jemand sie bauen muss.

## Offene Punkte

- `parser/mail.py` fehlt — Alert-Mails per IMAP ins Fundformat übersetzen
- **Karriereseiten- und jobs.ch-Abruf ist jetzt automatisiert** (`abruf.py`,
  siehe README) — kein Agent mehr nötig für Schritt 2-4 der alten
  Übergabe. Der Playwright-Pfad (14 JS-only-Firmen) ist nur ausserhalb
  dieser Sandbox getestet (siehe README, Abschnitt "Bekannte Lücke").
  9 von 90 Karriereseiten/jobs.ch-Kombinationen lieferten beim Testlauf vom
  10.09. `FEHLER — Struktur nicht erkannt` — die generische Heuristik
  erkennt kein Job-Href-Muster; wer Zeit hat, kann für genau diese Firmen
  einen eigenen Extractor in `fetch/` ergänzen: SGS, Stäubli, Accelleron,
  Baumer, Interroll, Kistler (plus Hitachi Energy/Hilti: HTTP 403, Swatch:
  Timeout — eher Bot-Abwehr als Strukturproblem).
- Priorisierung läuft jetzt über `daten/Zielliste_CH_Industrie.xlsx`
  (Spalte Prio) + `python tools/sync_quellen.py` — nicht mehr `quellen.json`
  von Hand editieren, das wird komplett überschrieben.
- **Omya** (Oftringen AG, Spezialchemie, Milliardenumsatz) fehlt in der
  Zielliste und gehört als Prio 1 rein
- Kistler und Leica Geosystems: Inserate nie inhaltlich geprüft
