# parser/

`mail.py` liest die Alert-Mails von jobs.ch (`jobmail@jobs.ch`) und
LinkedIn (`jobalerts-noreply@linkedin.com`, `jobs-noreply@linkedin.com`)
per IMAP aus dem jobradar-Postfach und schreibt sie ins Fundformat von
`radar.py`.

```bash
IMAP_USER=jan.jobradar@gmail.com IMAP_PASS=<App-Passwort> \
python parser/mail.py --seit 1 --out lauf_mail.json
python radar.py ingest lauf_mail.json
python radar.py excel Job_Radar.xlsx
```

**Nur lesen, siehe CLAUDE.md Regel 1.** IMAP `EXAMINE` (nie `SELECT`) plus
`BODY.PEEK[]` beim Fetch — doppelt abgesichert, keine `\Seen`-Flags, kein
Loeschen, kein Archivieren.

Gegen echte Mails aus dem jobradar-Postfach entwickelt und getestet (siehe
`tests/test_mail_parser.py` + `tests/fixtures/`). Format, Stand 10.09.2026:

**jobs.ch** (`jobmail@jobs.ch`): Liste im Body, ein Eintrag pro Zeile:
`- <Titel>, <Firma>, <Ort[, Ort...]>` gefolgt von der URL in der naechsten
Zeile. Bisher nur "Alert wurde aktiv"-Mails beobachtet (die Alerts sind
neu) — kein laufendes "N neue Jobs"-Digest. Taucht so eine Mail mit
anderem Format auf: hier dazulegen, nicht raten.

**LinkedIn** (beide Absender): Ein Kartenblock pro Treffer, durch eine
Trennzeile abgetrennt: `<Titel>\n<Firma>\n<Ort>\n` optional gefolgt von
1-3 Metazeilen, dann `Jobangebot ansehen: <url>`. `jobs-noreply` laesst
die Metazeilen meist weg, `jobalerts-noreply` haengt oft "X Kontakte"
o.ae. an — der Parser behandelt beides gleich.

Beobachtete Absender im jobradar-Postfach:
- jobmail@jobs.ch            — Job-Alarm, ein Mail pro Abo
- jobalerts-noreply@linkedin.com — gespeicherte Suche "Jobs in Schweiz"
- jobs-noreply@linkedin.com  — "aehnliche Jobs wie ..." / Empfehlungen
- newsletters-noreply@linkedin.com — RAUSCHEN, ignorieren
- willkommen@my.jobs.ch, no_reply@jobs.ch — RAUSCHEN, ignorieren
