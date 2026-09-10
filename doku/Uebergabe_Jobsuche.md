# Übergabe — Jobsuche Jan Lenz
Stand: 4. September 2026

Dieses Dokument enthält alles, was eine neue Sitzung braucht, um ohne Rückfragen weiterzuarbeiten.

---

## 1. Ziel

Jan (Project Leader bei Roland Berger, Meilen ZH) will aus der Beratung in eine **Commercial-, Strategie- oder Transaktionsrolle in der Schweizer Industrie** wechseln. Gebaut wird ein persönliches Screening-System: Zielliste + automatischer täglicher Job-Radar.

---

## 2. Was existiert

**a) Zielliste** — `Zielliste_CH_Industrie.xlsx`, 203 Firmen, 3 Blätter (Zielliste, Legende & Kriterien, Ausgeschlossen).

Spalten: Nr · Prio · Unternehmen · Ort · Kanton · Segment · Produkt · Umsatz · Whg · Umsatz CHF (Formel) · Grössenklasse (Formel) · GJ · Mitarbeiter · Eigentümer · Datenqualität · Kategorie · Mandat/Hinweis · **Fit-Score** · **Kontakt im Netzwerk** · **Status** · **Notizen** (gelb, von Jan auszufüllen) · Quelle · jobs.ch-Suchbegriff · jobs.ch-Suche (Link) · Karriereseite (geprüft).

Fünf Gruppen: Kern (weiss) · Grosskonzern (grün) · Liechtenstein (orange) · Konzern-HQ CH (violett) · Rohstoffhandel (grau).
Prio-Verteilung: **52 / 38 / 113**. Prio 3 ist nur Nachschlagewerk, wird nicht überwacht.

**Die Datei liegt nur im Session-Container** — Jan muss sie vor dem Löschen der Historie heruntergeladen haben. Sie ist die einzige nicht rekonstruierbare Arbeit.

**b) Geplante Aufgabe** „Job-Radar Schweizer Industrie" — werktags 05:00 UTC (07:00 Zürich), Push-Benachrichtigung, Gmail-Connector angehängt. Läuft serverseitig, unabhängig von der Sitzung.

**c) Postfach** `jan.jobradar@gmail.com` — eigenes Konto nur für Job-Alerts, bei LinkedIn als Primäradresse hinterlegt. Der Gmail-Connector in der Sitzung zeigt auf dieses Konto (nicht auf Jans persönliches).

---

## 3. Jans Kriterien

- **Zielprofil**: Schweizer Industrieunternehmen mit engineered product, CHF 100 Mio.–3 Mrd. Auf seinen Wunsch sind Grosskonzerne, Liechtenstein, Rohstoffhandel und ausländische Konzern-HQs in der Schweiz ebenfalls in der Liste.
- **Rollen**: Commercial (GTM, Pricing, Key Account, Vertriebsleitung) **und** Strategie/Transaktionen (Corporate Development, M&A, PMI). Stufe Manager bis Head of / Director. Kein C-Level bei Grosskonzernen, keine Sachbearbeiter- oder Junior-Rollen.
- **Geografie**: Meilen am Zürichsee. Romandie und Tessin praktisch draussen. Kleine Firmen unter ~800 Mitarbeitenden interessieren ihn nicht, auch in der Nähe nicht.
- **Kein Interesse** an Firmennachrichten, Führungswechseln oder Marktbeobachtung — er will ausschliesslich offene Stellen sehen.
- **Postfach-Regeln** (für ein anderes, noch offenes Thema): nach Typ labeln, grosszügig archivieren, **nie löschen**, alles von echten Menschen unangetastet, Schnitt bei drei Monaten.

---

## 4. Offene Punkte

| # | Was | Wer |
|---|---|---|
| 1 | **Neuen Aufgaben-Prompt einspielen** (Abschnitt 5 unten). Die Aufgabe läuft aktuell noch ohne die 38 Karriereseiten. | Claude |
| 2 | Zwei LinkedIn-**Firmen-Alerts** anlegen (Prio-1-Mittelständler, Prio 2). Die bestehenden Alerts sind zu breit — es kommen ABB-IT-Stellen und AWS durch. | Jan |
| 3 | Optional zwei jobs.ch-Alerts (`commercial excellence`, `corporate development`) — weitgehend redundant. | Jan |
| 4 | **Spalte S: Netzwerkkontakte** für die Prio-1-Firmen. Die einzige Aufgabe, die nur Jan erledigen kann, und die wertvollste. | Jan |
| 5 | Ersten Lauf am Montag auswerten, Filter nachschärfen. | beide |
| 6 | Jans **persönliches Gmail** ist überquellend und wurde nie aufgeräumt — der ursprüngliche Auftrag. Braucht einen Connector-Wechsel auf jenes Konto. | beide |

---

## 5. Der neue Aufgaben-Prompt

Vollständig, zum unveränderten Einspielen per `update_trigger` (oder `create_trigger`, falls die Aufgabe verschwunden ist — dann Cron `0 5 * * 1-5`, Push an, Name „Job-Radar Schweizer Industrie").

**Bekanntes Problem:** Das Trigger-Backend fällt zeitweise aus — `list_triggers` liefert leer, `update_trigger` scheitert mit „not found". Das löst sich nach einigen Minuten von selbst. Nicht sofort neu anlegen, sonst entstehen Doubletten.

```
Du erstellst für Jan Lenz seinen werktäglichen Job-Radar. Antworte auf Deutsch.

**Zu Jan:** Project Leader bei Roland Berger, wohnt bei Meilen am Zürichsee, ETH-Maschinenbau, sechs Jahre Commercial-Strategy-Beratung (Pricing, Go-to-Market, Vertriebsorganisation, Key Account Management), davor Simon-Kucher und Sensirion (dort Post-IPO-M&A und Produktionsprozesse). Kundenarbeit vor allem Industrie: Gabelstapler-OEMs, Materialflusstechnik, Elektrowerkzeuge, Sensorik; dazu Financial Services und Private Equity. Er will aus der Beratung in eine Commercial-, Strategie- oder Transaktionsrolle in der Schweizer Industrie wechseln.

**Diese Aufgabe sucht ausschliesslich offene Stellen.** Keine Firmennachrichten, keine Führungswechsel, keine Marktbeobachtung.

Drei Quellen: die Karriereseiten der Prio-1-Firmen (Schritt 2), jobs.ch (Schritte 3 und 4) und Jans Alert-Postfach (Schritt 5).

## Schritt 1 — Was ist heute fällig?

`date +%A` ausführen:
- **Jeden Werktag:** Schritt 2, 4 und 5
- **Montag, Mittwoch, Freitag:** zusätzlich Schritt 3

## Schritt 2 — Karriereseiten der Prio-1-Firmen (täglich, wichtigste Quelle)

Diese 38 URLs wurden am 04.09.2026 einzeln getestet und lieferten echte Stellenlisten. Sie sind der jobs.ch-Suche deutlich überlegen: bei Tecan zeigte jobs.ch 4 Stellen, die eigene Seite 37 — die interessanten Commercial-Rollen standen nur dort.

WebFetch pro URL, **in parallelen Gruppen von 8 bis 10**, mit dem Prompt: "Liste die offenen Stellen mit Titel, Ort und Datum. Nur Stellen in der Schweiz sind relevant, aber nenne sie alle, wenn nicht filterbar. Wenn nichts sichtbar ist, antworte KEINE STELLENLISTE."

Hitachi Energy — https://careers.hitachi.com/search/hitachi-energy/jobs/in/country/switzerland
Holcim — https://careers.holcimgroup.com/search/
Liebherr — https://www.liebherr.com/de/deu/karriere/offene-stellen/offene-stellen.html
Schindler — https://job.schindler.com/search/
SGS — https://careers.smartrecruiters.com/SGS
Hilti — https://careers.hilti.group/en-us/jobs/
Swatch Group — https://www.swatchgroup.com/en/job-finder
Clariant — https://careers.clariant.com/search/
Stadler Rail — https://jobs.stadlerrail.ch/
Sonova — https://jobs.sonova.com/go/All-Jobs/4577301/
Mettler-Toledo — https://jobs.mt.com/en/search-jobs
Stäubli — https://careers.smartrecruiters.com/staubligroup
Alstom — https://jobsearch.alstom.com/search/
Belimo — https://www.jobs.ch/en/companies/16954-belimo-automation-ag/
Dätwyler — https://careers.datwyler.com/search/
VAT Group — https://careers.vatvalve.com/search/
Bossard — https://www.jobs.ch/en/companies/3501-bossard-ag/
Burckhardt Compression — https://careers.burckhardtcompression.com/search/
Accelleron — https://www.jobs.ch/en/companies/125399-accelleron-industries/
Landis+Gyr — https://careers.landisgyr.com/search/
Tecan — https://careers.tecan.com/search/
HUBER+SUHNER — https://recruiting.hubersuhner.com/Jobs/All?lang=de
Ivoclar — https://www.jobs.ch/en/companies/6731-ivoclar-vivadent-ag/
Rieter — https://live.solique.ch/rieter/en/internet
maxon — https://recruiting.maxongroup.com/Jobs/All?lang=de
Komax — https://www.jobs.ch/de/firmen/791-komax-group/stellenangebote/
Baumer — https://jobs.baumer.com/
Interroll — https://www.interroll.com/company/careers/
Meier Tobler — https://www.jobs.ch/en/companies/85876-meier-tobler-ag/vacancies/
Kistler — https://www.kistler.com/CH/de/kistler-stellenangebote/jobs
Reishauer — https://jobs.reishauer.com/search/?locale=de_DE
Sensirion — https://sensirion.com/career
Ferag — https://recruitingapp-2970.umantis.com/Jobs/1?CompanyID=1
Angst+Pfister — https://www.jobs.ch/de/firmen/4422-angst-pfister-ag/stellenangebote/
Haag-Streit (Metall Zug) — https://www.jobs.ch/en/companies/813-haag-streit-ag/
Bruker BioSpin — https://www.jobs.ch/en/companies/32002-bruker-biospin-ag/
Santrade / Sandvik — https://www.home.sandvik/en/careers/job-search/
ABB — https://www.jobs.ch/en/companies/55089-abb-schweiz-ag/

**Diese 14 Prio-1-Firmen haben keine abrufbare Karriereseite** (Workday und ähnliche geben ihre Listen nur per JavaScript aus). Für sie stattdessen die jobs.ch-Stichwortsuche aus Schritt 4 als einzige Quelle nutzen und sie NICHT einzeln abfragen: Amcor, Sika, STMicroelectronics, Alcon, Garmin, Georg Fischer, Logitech, Endress+Hauser, Sulzer, Geberit, Bucher Industries, Bühler, Kardex, HOERBIGER.

## Schritt 3 — jobs.ch, Firmensuche Prio 2 (Montag, Mittwoch, Freitag)

Pro Firma ein WebFetch auf `https://www.jobs.ch/de/stellenangebote/?term=<FIRMENNAME URL-kodiert>`.

**URL-Regeln:** Sonderzeichen durch ein Leerzeichen (%20) ersetzen, nicht kodieren — "Angst+Pfister" muss `Angst%20Pfister` heissen. Keinen `page`-Parameter.

**Fetch-Prompt:** "Liste ALLE Stellen, bei denen der Arbeitgeber tatsächlich <FIRMA> ist, mit Titel, Ort, Alter und Link. Stellen anderer Arbeitgeber ignorierst du. Wenn keine dabei ist, antworte KEINE ERGEBNISSE."

**PRIO 2 (38):** ams-OSRAM, SFS, SIG, dormakaba, United Grinding, Ammann, Forbo, Hamilton, Schweiter, Ypsomed, Zehnder, Phoenix Mecano, Jura Elektroapparate, Feintool, Sauter, Arbonia, Cicor, Bystronic, V-ZUG, INFICON, medmix, Beyond Gravity, Weidmann, SKAN, Sefar, Gurit, Ascom, Güdel, u-blox, Zünd, Leister, Uster Technologies, Bruderer, Hunkeler, Leica Geosystems, Everllence, Glencore, MET Group

## Schritt 4 — jobs.ch, Stichwortsuche (täglich, 18 Suchen)

WebFetch, OHNE sort-Parameter. Diese Suche deckt die 14 Firmen ohne Karriereseite ab und findet Firmen, die noch nicht auf Jans Liste stehen — solche Neuentdeckungen ausdrücklich als neu kennzeichnen.

Breit (viele Treffer, streng filtern):
- https://www.jobs.ch/de/stellenangebote/?term=business%20development
- https://www.jobs.ch/de/stellenangebote/?term=leiter%20strategie

Commercial:
- https://www.jobs.ch/de/stellenangebote/?term=go-to-market
- https://www.jobs.ch/de/stellenangebote/?term=commercial%20excellence
- https://www.jobs.ch/de/stellenangebote/?term=head%20of%20sales
- https://www.jobs.ch/de/stellenangebote/?term=vertriebsleiter
- https://www.jobs.ch/de/stellenangebote/?term=pricing%20manager
- https://www.jobs.ch/de/stellenangebote/?term=key%20account%20manager
- https://www.jobs.ch/de/stellenangebote/?term=business%20development%20manager
- https://www.jobs.ch/de/stellenangebote/?term=sales%20transformation

Strategie und Transaktionen:
- https://www.jobs.ch/de/stellenangebote/?term=corporate%20development
- https://www.jobs.ch/de/stellenangebote/?term=strategie%20manager
- https://www.jobs.ch/de/stellenangebote/?term=head%20of%20strategy
- https://www.jobs.ch/de/stellenangebote/?term=mergers%20acquisitions
- https://www.jobs.ch/de/stellenangebote/?term=post%20merger%20integration
- https://www.jobs.ch/de/stellenangebote/?term=integration%20manager
- https://www.jobs.ch/de/stellenangebote/?term=transformation%20manager
- https://www.jobs.ch/de/stellenangebote/?term=business%20transformation

## Schritt 5 — Alert-Postfach auslesen (täglich)

Jans LinkedIn-Alerts laufen in `jan.jobradar@gmail.com` ein. Mit den Gmail-Werkzeugen:
- `from:jobalerts-noreply@linkedin.com newer_than:2d` — seine gespeicherten Alerts, wichtigste Mail-Quelle
- `from:jobs-noreply@linkedin.com newer_than:2d` — LinkedIn-Empfehlungen, schwächere Qualität
- `from:jobs.ch newer_than:2d` — falls er dort Alerts angelegt hat

Gefundene Mails mit `get_thread` öffnen und Titel, Firma, Ort, Link herausziehen.

**Vollständig ignorieren** (Netzwerkrauschen, keine Stellen): `invitations@linkedin.com`, `notifications-noreply@linkedin.com`, `messages-noreply@linkedin.com`, `career-interests-noreply@linkedin.com`, `security-noreply@linkedin.com`, alles von Google.

LinkedIn wiederholt dieselbe Stelle über mehrere Tage — entdoppeln.

**Im Postfach nichts verändern.** Nicht löschen, nicht archivieren, nicht als gelesen markieren. Nur lesen.

## Schritt 6 — Filtern

Nur Stellen behalten, die ALLE drei Bedingungen erfüllen:

1. **Alter**: höchstens 10 Tage. Wo kein Datum sichtbar ist (manche Karriereseiten zeigen keins), die Stelle aufnehmen und "Datum unbekannt" dazuschreiben.
2. **Passende Funktion** — zwei gleichwertige Familien:
   - *Commercial*: Vertrieb, Go-to-Market, Pricing, Key Account, Business Development, Commercial Excellence, Vertriebsstrategie, Marktentwicklung, kaufmännische Produktverantwortung, Marketingleitung.
   - *Strategie und Transaktionen*: Unternehmensstrategie, Corporate Development, M&A, Post-Merger-Integration, Integrationsmanagement, Transformationsprogramme, Portfoliomanagement, Beteiligungsmanagement.

   RAUS: Ingenieurs-, Produktions-, IT-, Logistik-, HR-, Finanz-, Einkaufs-, Qualitäts- und Servicetechnikerrollen, Lehrstellen, Praktika, Verkaufspersonal im Detailhandel.

   Vier bekannte Fallen: "Integration Manager", "Transformation Manager" und "Digital Technology Manager" sind auf Schweizer Portalen mehrheitlich IT-Rollen. "Business Development" trägt bei Personaldienstleistern, Versicherungen, Speditionen und Agenturen oft eine reine Akquiserolle im Titel. Und ein technischer Investitionsgüter-Verkäufer ("Sales Manager" mit Reisetätigkeit und Branchenvorkenntnis als Anforderung) ist keine Commercial-Führungsrolle — höchstens ein Grenzfall.
3. **Passende Stufe**: Manager, Senior Manager, Head of, Director, Leiter/in, Bereichsleitung. RAUS: Sachbearbeiter, Spezialist, Junior, Trainee, und reine C-Level-Rollen bei Grosskonzernen.

Nur Schweizer Standort, nur Industrie- und Produktionsunternehmen. Banken, Versicherungen, Beratungen, Personaldienstleister, Speditionen, Detailhandel, öffentliche Verwaltung, Gesundheitsdienstleister und reine Tech-/Cloud-Konzerne raus.

**Geografie.** Jan wohnt bei Meilen am Zürichsee. Romandie und Tessin nur bei aussergewöhnlich guter Passung, und dann unter den Grenzfällen. Deutschschweiz und Innerschweiz unproblematisch. Die Karriereseiten liefern viele Auslandsstellen — die konsequent weglassen.

**Deckelung bei den Grosskonzernen.** ABB, Holcim, Sika, Schindler, SGS, Swatch, Logitech, Clariant, Sonova, Geberit, Alcon, Amcor, Hilti, Stadler Rail, Sulzer, Georg Fischer, STMicroelectronics, Mettler-Toledo, Alstom und Sandvik haben permanent dutzende offene Stellen. Dort besonders streng filtern, **höchstens zwei Treffer pro Konzern**.

**Quellenübergreifend entdoppeln.** Eine Stelle, die in mehreren Quellen auftaucht, erscheint einmal — mit dem Hinweis, aus welchen.

## Schritt 7 — Beratungshintergrund prüfen

Für jeden Treffer, der höchstens 3 Tage alt ist, die Anzeige per WebFetch öffnen: "Nenne die geforderten Qualifikationen und Erfahrungen wörtlich. Wird Beratungserfahrung oder ein Consulting-Hintergrund erwähnt? Antworte mit JA oder NEIN und dem betreffenden Satz."

Treffer mit Beratungsbezug — "Unternehmensberatung", "Beratungserfahrung", "consulting background", "Strategieberatung", "Big 4" — mit **[Consulting gesucht]** markieren und ganz nach oben stellen.

Das Anforderungsprofil auch zur Fehltrefferkontrolle nutzen: verlangt die Stelle vor allem Branchen- und Produktkenntnis statt Führungs- und Konzeptarbeit, passt sie trotz gutem Titel nicht.

Höchstens 12 Anzeigen im Detail öffnen. LinkedIn-Anzeigen lassen sich oft nicht öffnen — dann ohne Detailprüfung aufführen und das dazusagen.

## Schritt 8 — Ausgeben

Ein Einleitungssatz: welche Quellen gelaufen sind, wie viele Karriereseiten und Firmen geprüft, wie viele Alert-Mails gelesen, wie viele Treffer. Nenne auch, wie viele Karriereseiten nicht erreichbar waren.

Dann zwei Abschnitte:

**„Neu" (höchstens 3 Tage alt)** — ausführlich. Pro Treffer:
**Stellentitel** — Firma, Ort · vor X Tagen · Quelle · ggf. **[Consulting gesucht]**
Ein bis zwei Sätze: warum das passt und was auffällt. Bei Bezug zu seiner bisherigen Arbeit — Intralogistik, Materialfluss, Sensorik, Werkzeuge, Private Equity — das dazusagen. Link zur Anzeige.

**„Weiterhin offen" (4 bis 10 Tage)** — knapp. Eine Zeile pro Stelle: Titel, Firma, Ort, Alter, Link.

Zum Schluss maximal drei Grenzfälle unter "Nicht ganz, aber erwähnenswert".

**Keine Treffer ist ein gültiges Ergebnis.** Dann in zwei Sätzen sagen und aufhören. Nichts erfinden, die Liste nicht mit schlecht passenden Stellen strecken.

## Regeln

- Nur wiedergeben, was du tatsächlich auf den Seiten oder in den Mails gesehen hast. Keine Stelle aus dem Gedächtnis, keine geratenen Links.
- Karriereseiten ändern ihre URLs. Liefert eine 404 oder plötzlich nichts mehr, notiere das am Schluss unter "Quellen, die heute nicht funktioniert haben" — Jan lässt sie dann ersetzen.
- Kein LinkedIn- und kein Indeed-Scraping. LinkedIn-Stellen kommen ausschliesslich aus den Alert-Mails.
- Kurz halten. Er liest das morgens vor der Arbeit. Fünf gut begründete Treffer schlagen zwanzig aufgezählte.
```

---

## 6. Gelernte Fallstricke

**jobs.ch**
- `?term=X` funktioniert; `&region=` läuft in eine Redirect-Schleife.
- `&page=2` liefert nur Fremdtreffer — die echten Firmenstellen stehen alle auf Seite 1.
- `sort=date` zerstört die Relevanz; Datumssortierung nicht verwenden.
- Ein `+` im Firmennamen (`Angst%2BPfister`) liefert **null** Treffer — durch `%20` ersetzen.
- Die Trefferliste mischt Fremdfirmen unter; im Fetch-Prompt explizit nach dem Arbeitgeber filtern lassen, sonst wird gezählt, was nicht dazugehört.
- Firmen-**Profilseiten** (`/companies/…`) sind sauberer als die Stichwortsuche.
- Bei einigen Firmen ist der Suchbegriff ein anderer als der Firmenname: Metall Zug → **Haag-Streit**, Bucher Industries → **Bucher Municipal**. Landis+Gyr schreibt auf jobs.ch gar nicht aus.

**Karriereseiten**
- Workday, Eightfold und einige SuccessFactors-Instanzen rendern die Liste nur per JavaScript — per WebFetch nicht erreichbar. Das betrifft 14 der 52 Prio-1-Firmen.
- Der Test lohnt sich: Tecan hatte auf jobs.ch 4 Stellen, auf der eigenen Seite 37 — inklusive zweier Commercial-Rollen, die auf jobs.ch fehlten.

**LinkedIn**
- Kein Scraping (ToS, und die Tools blockieren es). Der Weg führt über Alert-Mails ins Postfach.
- Der Firmenfilter in der Jobsuche zeigt nur Firmen, die **gerade** ausschreiben — Firmen ohne aktuelle Stellen lassen sich nicht vormerken.
- Der „Job-Alert erstellen"-Knopf auf Firmenseiten wurde bei vielen Nutzern durch „Ich bin interessiert" ersetzt und ist unzuverlässig.
- Freie Konten sind auf rund 10 aktive Alerts begrenzt.
- Die Ergebnisseite mit den Filtern erscheint erst nach einer Suche; `linkedin.com/jobs/search/?keywords=&location=Schweiz` führt direkt dorthin.

**Datenlage**
- Rund ein Drittel der privaten Schweizer Industriefirmen publiziert keine Umsatzzahlen. In der Liste steht dort eine Grössenordnung, kein Fakt — Spalte „Datenqualität" beachten, nie in einer Bewerbung zitieren.

---

## 7. Was der neue Chat nicht neu erfragen muss

Jans Profil, Kriterien, Postfach-Regeln und der Aufbau des Radars stehen bereits im Langzeitgedächtnis (`/profile.md`, `/topics/career-transition.md`, `/topics/email.md`). Eine neue Sitzung kennt ihn also.

Was **nicht** überlebt: die Excel-Datei im Container und die Build-Skripte. Jan muss die Datei vorher heruntergeladen und beim nächsten Mal wieder hochgeladen haben.
