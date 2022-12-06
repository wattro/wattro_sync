# Wattro Sync Helfer

Scriptsammlung, um das Synchronisieren von Daten aus einer lokalen Quelle nach Wattro zu
erleichtern.

## Voraussetzung

* Verbindung zu wattro (https) und Quellsystem
* python >= 3.10 und pip

## Installation

* `pip install wattro-sync`

## Anwendung

Nach der Installation können die Scripte
mit `python -m wattro_sync.[script_name] [Argumente]` aufgerufen werden.
Etwa: `python -m wattro_sync.setup asset SQLite`

### Die zentrale Konfigurationsdatei

Die Synchronisation beruht auf einer Konfigurationsdatei, welche mit `setup` erzeugt
oder aktualisiert werden kann.
Die Konfigurationsdatei kann auch von Hand angepasst werden.
Mit `sync --dry` kann geprüft werden, ob die Synchronisation wie erwartet arbeitet.

`setup` erwartet zwei Argumente:

* das Daten-Ziel (zum Beispiel 'asset': Geräte, die mit Wattro verwaltet werden)
* der Daten Quelltyp (zum Beispiel 'Benning' für eine Benning Datenbank)

Im Prozess werden je nach Ziel und Quelltyp verschiedene Eingaben abgefragt und die
Datenverfügbarkeit geprüft.
Nur gültige Werte werden in die Konfigurationsdatei geschrieben.

#### Mail Infos

Um Informationen zum Erfolg der Synchornisation zu bekommen, können Mails verschickt
werden.
Das "log_level" entspricht dabei einem numerischen Wert nach
dem [Python Log Level Schema.](https://docs.python.org/3/library/logging.html#logging-levels)

Insbesondere:

| Level | numerischer Wert | Mail wird versendet bei...  |
|-------|------------------|-----------------------------|
| ERROR | 40               | Fehler beim Synchronisieren |
| INFO  | 20               | Änderung von Datensätzen    |
| DEBUG | 10               | Aufruf des Scripts          |

### Synchronisation

Mit `sync` werden die Daten synchronisiert.
Die Synchronisation kann auch eingeschränkt, verbos oder als dry run durchgeführt
werden.
`sync --help` für mehr.

# Development

## Pre Commit tooling

```bash
# requires black, mypy and bandit to be installed (via pip)
# none of the following commands should produce output on the second run.
# lint
black wattro_sync -q
# search for typing issues
mypy wattro_sync --no-error-summary --config-file mypy.ini
# search for common issues
bandit -r wattro_sync -c bandit.yaml -q
```

## Build

```bash
# requires build and twine to be installed (via pip)
python -m build
twine upload dist/*
```