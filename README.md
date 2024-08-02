# mass-mail
E-Mails an zahlreiche ausgewählte Fachschaften versenden

## Set-Up

Erstelle eine Datei `config.json` in diesem Ordner mit dem folgenden (angepassten) Inhalt:

```json
{
  "from_name": "🤖 Fachschaftenreferat AStA Uni Bonn",
  "mail_user": "fsen@example.org",
  "mail_host": "mail.example.org"
}
```

Erstelle ein virtualenv und installiere die Abhängigkeiten darin:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Um die Skripte auszuführen, aktiviere lediglich zuvor das virtualenv:

```shell
source venv/bin/activate
```


## Bedienung

Der Versand von E-Mails an ausgewählte Fachschaftsadressen geschieht in drei Schritten

1. Vorbereiten des Templates
2. Vorbreiten der Fachschaftsdaten (id, name, adressen, ggf. weitere Felder)
3. Versand der E-Mails (dry-run)
4. Versand der E-Mails (in echt)


### Vorbereiten des Templates

In `templates` wird eine neue Datei angelegt.
Die erste Zeile ist der Betreff,
die zweite Zeile bleibt leer,
ab der dritten Zeile folgt der Inhalt der E-Mail.
Platzhalter werden mit geschweiften Klammern dargestellt.
Um zum Beispiel später den Namen der Fachschaft darzustellen, wird {fs_name} eingefügt.
Die Platzhalter entsprechen dabei den Spaltennamen in der Eingabe-TSV-Datei.


### Vorbreiten der Fachschaftsdaten (id, name, adressen, ggf. weitere Felder)

Als Eingabe dient eine TSV-Datei (tab separated values).
Pflichtspalten sind `fs_id`, `fs_name`, `addresses`.
Weitere Spalten können hinzugefügt und im Template verwendet werden.

Das Skript `grab-data.py` fragt diese Daten von fsen.datendrehschei.be ab.
Es kann nach dem Start des Haushaltsjahres filtern sowie verschiedene Kategorien von E-Mail-Adressen ausgeben.

Beispiele:

```shell
# Alle Fachschaften mit der E-Mail-Adresse für Finanzen und für die fsl und den Kontakt ausgeben
./grab-data.py --categories kontakt fsl

# Fachschaften, deren Haushaltsjahr am 01.04. beginnt, mit der finanzen-Adresse ausgeben
./grab-data.py --financial-year-start 01.04. --categories finanzen

# Fachschaften, die einen offenen AFSG-Antrag für das Sommersemester 2024 haben, mit der finanzen-Adresse ausgeben
# (gibt zusätzliche Spalte request_id aus)
./grab-data.py --open-afsg 2024-SoSe --categories finanzen

# Fachschaften, die einen offenen AFSG-Antrag für das Sommersemester 2024 haben, mit der finanzen-Adresse ausgeben
# (gibt zusätzliche Spalte request_id aus)
./grab-data.py --open-afsg 2024-SoSe --categories finanzen

# Fachschaften, die noch keinen AFSG-Antrag für das Sommersemester 2024 gestellt haben, mit der finanzen-Adresse ausgeben
# (gibt zusätzliche Spalte request_id aus)
./grab-data.py --no-afsg 2024-SoSe --categories finanzen

# Für jede Fachschaft die Berechtigungen abrufen und mit der kontakt-Adresse ausgeben
# (gibt zusätzliche Spalte permissions aus, welche von send-mail.py in Tabellenform gebracht wird)
./grab-data.py --categories kontakt --permissions
```

Weitere benötigte Spalten können manuell hinzugefügt werden.


### Versand der E-Mails (dry-run)

Das Skript `send-mail.py` versendet die E-Mails.
Vor dem eigentlichen Versand wird mit dem Parameter `--dry-run` ein Durchlauf durchgeführt, ohne die E-Mails tatsächlich zu versenden.
Stattdessen werden sie als .eml-Dateien in einem Ordner gespeichert.
```shell
# Dry-Run durchführen und die .eml-Dateien im Ordner test speichern.
./send-mail.py --dry-run ./test addresses.tsv templates/2023-03-08-antragsfrist-reminder.txt 
```

### Versand der E-Mails (in echt)

Ohne den `--dry-run`-Parameter fragt das Skript `send-mail.py` das E-Mail-Passwort ab und sendet dann die E-Mails.
Zudem werden sie im Gesendete-E-Mails-Ordner abgelegt.
```shell
# E-Mails versenden
./send-mail.py addresses.tsv templates/2023-03-08-antragsfrist-reminder.txt 
```
