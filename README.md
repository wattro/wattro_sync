# Wattro Sync

Ermöglicht es, Daten aus einer lokalen Quelle mit Wattro zu synchronisieren.

## Voraussetzung

* Verbindung zu wattro (https) und Quellsystem
* python >= 3.10 und pip

## Installation

* `pip install wattro-sync`

## Einrichten

### Die zentrale Konfigurationsdatei

Die Synchronisation beruht auf einer Konfigurationsdatei, welche mit `python -m wattro_sync.setup ZIEL QUELLE` erzeugt
oder aktualisiert werden kann (siehe `python -m wattro_sync.setup --help` für alle gültigen Optionen).

Im Prozess werden je nach Ziel- und Quelltyp verschiedene Eingaben abgefragt und die
Datenverfügbarkeit geprüft.
Nur gültige Werte werden in die Konfigurationsdatei geschrieben.

*ACHTUNG* 

Für Importe aus Mosaik muss aus technischen Gründen ein View angesporchen werden, welcher 
* die Datensätze auf maximal 2k beschränkt und 
* die Datensätze nach Änderungsdatum sortiert

Die Konfigurationsdatei kann von Hand angepasst werden.
Mit `python -m wattro_sync.sync --dry` kann geprüft werden, ob die Synchronisation wie erwartet arbeitet.

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

## Synchronisation

Mit `python -m wattro_sync.sync` werden die Daten synchronisiert.
Siehe `python -m wattro_sync.sync --help` für mehr.

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