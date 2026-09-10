# Umzug nach Claude Code — Anleitung

Alles, was bisher in der Cloud-Session lag, ist in diesem Ordner. Er ist
vollständig: ohne die alte Unterhaltung geht nichts verloren.

---

## Schritt 1 — Ordner ablegen

Zip entpacken und den Ordner dorthin legen, wo du deine Projekte hast,
zum Beispiel `~/Projekte/job-radar`.

## Schritt 2 — Repo anlegen und pushen

Claude Code im Ordner starten und sagen:

```
Mach aus diesem Ordner ein privates GitHub-Repo "job-radar"
unter jlenz1742 und pushe alles.
```

Falls du es lieber selbst machst:

```bash
cd ~/Projekte/job-radar
git init && git add -A && git commit -m "Job-Radar: Stand Dry Run 10.09.2026"
gh repo create job-radar --private --source=. --push
```

**Privat lassen.** Im Repo stehen deine Zielfirmen, deine Bewertungen und
später deine Bewerbungsnotizen.

## Schritt 3 — Prüfen, dass die Maschine läuft

```bash
pip install -r requirements.txt
python radar.py neu
python radar.py excel Job_Radar.xlsx
```

`python radar.py neu` muss beim ersten Mal **nichts** ausgeben — der Dry Run
ist als Bestand aufgenommen, nicht als Neuzugang. Wenn dort 54 Zeilen
erscheinen, stimmt etwas nicht.

## Schritt 4 — App-Passwort für das Postfach

Nur nötig, wenn der Radar später ohne dich laufen soll.

1. Bei `jan.jobradar@gmail.com` anmelden
2. Zweistufige Bestätigung aktivieren (Voraussetzung für App-Passwörter)
3. Unter myaccount.google.com/apppasswords ein App-Passwort erzeugen
4. Als GitHub-Secret hinterlegen: `IMAP_USER` und `IMAP_PASS`

**Nimm auf keinen Fall das Passwort deines privaten Kontos.** Ein
App-Passwort im Repo-Secret gewährt vollen Zugriff auf dieses Postfach.
Weil jobradar nur für diesen Zweck existiert und keine private Korrespondenz
enthält, ist das Risiko begrenzt — aber es ist eine bewusste Entscheidung.

## Schritt 5 — Mail-Parser bauen

Das ist der nächste echte Schritt. In Claude Code:

```
Lies CLAUDE.md und parser/README.md. Bau parser/mail.py: liest per IMAP
die Alert-Mails von jobs.ch und LinkedIn aus dem jobradar-Postfach der
letzten N Tage und schreibt sie ins Fundformat von radar.py.
Zugangsdaten aus IMAP_USER und IMAP_PASS.
Wichtig: Das Postfach wird NUR GELESEN. Nichts löschen, nichts archivieren,
nichts als gelesen markieren.
Schreib Tests mit echten, gespeicherten Beispielmails.
```

Danach ein Testlauf von Hand, bevor irgendetwas nach Actions geht.

## Schritt 6 — Actions scharf schalten

`.github/workflows/radar.yml` ist ein **ungetesteter Entwurf**. Erst
aktivieren, wenn Schritt 5 lokal sauber läuft. Der Workflow lässt den Lauf
absichtlich rot werden, wenn eine Quelle ausfällt — stilles Nichtstun ist
der Fehlerfall, den du nicht willst.

---

## Was in diesem Ordner liegt

| Datei | Was drin ist |
|---|---|
| `CLAUDE.md` | Projektanweisungen für Claude Code — Profil, Kriterien, Regeln, Fallstricke. **Wird automatisch gelesen.** |
| `radar.py` | Die Maschine: Normalisieren, Dedup, Zustand, Excel |
| `state.json` | Das Gedächtnis — 54 Stellen aus dem Dry Run |
| `Job_Radar.xlsx` | Arbeitsmappe: Neu · Alle Stellen · Quellen · Läufe |
| `lauf_2026-09-10.json` | Die Funde des Dry Runs als Eingabebeispiel |
| `daten/Zielliste_CH_Industrie.xlsx` | 203 Firmen, drei Prioritäten, mit Quellen |
| `daten/quellen.json` | 90 Quellen maschinenlesbar: 38 abrufbar, 14 JS-only, 38 ungeprüft |
| `doku/Dry_Run_2026-09-10.md` | Der komplette Dry Run mit allen Bewertungen |
| `doku/Uebergabe_Jobsuche.md` | Die ältere Übergabe mit Kriterien und Karriereseiten |
| `.github/workflows/radar.yml` | Actions-Entwurf, ungetestet |

## Was noch bei dir liegt

- **Google Drive:** Ordner `Job_Radar` mit dem Blatt `Job_Radar_Stellen`.
  Sobald das Repo läuft, ist die Excel im Repo die Quelle der Wahrheit —
  das Drive-Blatt kann als Lesekopie bleiben oder weg.
- **Alerts:** LinkedIn steht auf „sofort" und feuert alle zwei Stunden.
  Auf täglich stellen. Bei jobs.ch sind `Strategic Director` und
  `Strategy Director` doppelt, `Beratung / Unternehmensentwicklung` liefert
  genau die Beratungsstellen, von denen du weg willst.
- **Zwei Statusprüfungen:** Omya ist bestätigt abgelaufen. Trafag war auf der
  Seite als abgelaufen markiert — dort lohnt ein Anruf bei Katharina Zürrer.

## Die drei Stellen, die aus dem Dry Run übrig sind

1. **Stadler Rail — Project Manager Strategic Projects** (Frauenfeld) —
   inhaltlich die nächste an deiner Tätigkeit. Verlangt eine
   betriebswirtschaftliche Grundausbildung, das musst du im Anschreiben drehen.
   Stabsstelle ohne Führung.
2. **Ammann — Spare Parts Pricing Manager** (Langenthal, publiziert 09.09.) —
   fachlich ein Simon-Kucher-Mandat. Fachrolle ohne Führung, mit SAP- und
   Power-BI-Anteil; wahrscheinlich ein Schritt zurück bei Titel und Lohn.
3. **VAT Group — Sector Manager Go-to-Market** (Haag SG) — Titel und Sektor
   passen, aber sie wollen jemanden, der Channel-Netze selbst aufgebaut hat.
   Haag ist ab Meilen 1½ Stunden.
