# DMS Upload-Vorbereitung (Fabasoft)

Python-Tool mit grafischer Oberfläche (tkinter) zur Vorbereitung von Datei-Uploads in ein DMS (Fabasoft).

## Features

- **Quellordner scannen** – Rekursives Durchsuchen eines gewählten Ordners
- **Nicht-uploadfähige Dateien verschieben** – Dateien mit konfigurierbaren Endungen (z.B. `.exe`, `.bat`, `.lnk`) werden in einen Zielordner mit gespiegelter Ordnerstruktur verschoben
- **Upload-Pakete bilden** – Gültige Dateien werden in Pakete ≤ 1 GiB eingeteilt
- **Rekursive Aufteilung** – Ordner > 1 GiB werden automatisch auf Unterebenen aufgeteilt
- **CSV-Logfile** – Alle Aktionen werden dokumentiert
- **Trockenlauf-Modus** – Vorschau ohne tatsächliche Dateioperationen
- **Systemschutz** – Blockiert Systemordner (C:\Windows, Program Files etc.)
- **Konfigurierbar** – Endungen über JSON-Datei anpassbar

## Voraussetzungen

- Python 3.10+ (oder als EXE ohne Python-Installation)
- Keine externen Abhängigkeiten – nur Python-Standardbibliothek

## Ausführen

```bash
python main.py
```

## EXE bauen mit PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "DMS-Upload-Vorbereitung" main.py
```

Die fertige EXE liegt danach in `dist/DMS-Upload-Vorbereitung.exe`.

## Konfiguration

Beim ersten Start wird eine `dms_vorbereitung_config.json` neben dem Programm erstellt (falls noch nicht vorhanden). Die Endungsliste kann direkt im GUI bearbeitet und gespeichert werden.

```json
{
  "ungueltige_endungen": [
    ".bat",
    ".cmd",
    ".com",
    ".exe",
    ".js",
    ".lnk",
    ".msi",
    ".msp",
    ".ps1",
    ".psm1",
    ".vbs"
  ]
}
```

## Logfile-Format

```
DatumZeit;Aktion;Grund;OriginalPfad;NeuerPfad;DateigroesseBytes
2026-02-12 09:30:12;verschoben;ungueltige_endung:.exe;U:\FB51\tool.exe;U:\_Ziel\FB51\tool.exe;245760
```
