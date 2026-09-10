# parser/

Hier gehoert der Mail-Parser hin (`mail.py`): liest die Alert-Mails von
jobs.ch (`jobmail@jobs.ch`) und LinkedIn (`jobalerts-noreply@linkedin.com`,
`jobs-noreply@linkedin.com`) per IMAP aus dem jobradar-Postfach und schreibt
sie ins Fundformat von `radar.py`.

Noch nicht gebaut.

Beobachtete Absender im jobradar-Postfach (Stand 10.09.2026):
- jobmail@jobs.ch            — Job-Alarm, ein Mail pro Abo
- jobalerts-noreply@linkedin.com — Jobbenachrichtigung
- jobs-noreply@linkedin.com  — "aehnliche Jobs wie ..."
- newsletters-noreply@linkedin.com — RAUSCHEN, ignorieren
- willkommen@my.jobs.ch, no_reply@jobs.ch — RAUSCHEN, ignorieren
