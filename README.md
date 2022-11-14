# Wattro Sync Helfer

Scriptsammlung, um das Synchronisieren von Daten aus einer lokalen Quelle nach Wattro zu erleichtern.

## Voraussetzung
* Verbindung zu wattro (https) und Quellsystem
* python >= 3.10 und pip 

## Installation
* `pip install wattro_sync`

## Anwendung

Nach der Installation können die Scripte mit `python -m wattro_sync.[script_name] [Argumente]` aufgerufen werden.
Etwa: `python -m wattro_sync.setup asset SQLite`

### Die zentrale Konfigurationsdatei

Die Synchronisation beruht auf einer Konfigurationsdatei, welche mit `setup` erzeugt oder aktualisiert werden kann.
Die Konfigurationsdatei kann auch von Hand angepasst werden. 
Mit `sync --dry` kann geprüft werden, ob die Synchronisation wie erwartet arbeitet.


`setup` erwartet zwei Argumente: 
* das Daten-Ziel (zum Beispiel 'asset': Geräte, die mit Wattro verwaltet werden)
* der Daten Quelltyp (zum Beispiel 'Benning' für eine Benning Datenbank)
 
Im Prozess werden je nach Ziel und Quelltyp verschiedene Eingaben abgefragt und die Datenverfügbarkeit geprüft. 
Nur gültige Werte werden in die Konfigurationsdatei geschrieben.

### Synchronisation
Mit `sync` werden die Daten synchronisiert.
Die Synchronisation kann auch eingeschränkt, verbos oder als dry run durchgeführt werden.
`sync --help` für mehr.