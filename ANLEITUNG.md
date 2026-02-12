# Schnellstart-Anleitung

## Auf einem anderen Rechner verwenden

### 1. Repository klonen
```bash
git clone https://github.com/Benkei-dev/DMSUploadHelper.git
cd DMSUploadHelper
```

### 2. Python prüfen
Das Tool benötigt **Python 3.10 oder höher**.

Prüfen:
```bash
python --version
```

Falls Python fehlt: https://www.python.org/downloads/

### 3. Tool starten
```bash
python main.py
```

Das GUI-Fenster öffnet sich automatisch.

### 4. Verwendung
1. **Quellordner auswählen** – Der Ordner, dessen Dateien analysiert werden sollen
2. **Zielbasis auswählen** (optional) – Wohin nicht-uploadfähige Dateien verschoben werden. Standard: `_NichtUploadfaehig` im Quellordner
3. **Trockenlauf** aktivieren für eine Vorschau ohne Dateioperationen
4. **Analyse starten** klicken

### 5. EXE erstellen (optional – für Rechner ohne Python)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "DMS-Upload-Vorbereitung" main.py
```

Die fertige EXE liegt in `dist/DMS-Upload-Vorbereitung.exe` und kann ohne Python-Installation ausgeführt werden.

## Konfiguration anpassen

Die Datei `dms_vorbereitung_config.json` wird beim ersten Start automatisch erstellt. Du kannst sie auch manuell bearbeiten:

```json
{
  "ungueltige_endungen": [
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".ps1",
    ".psm1",
    ".vbs",
    ".js",
    ".msi",
    ".msp",
    ".lnk"
  ]
}
```

Oder direkt im GUI über die Endungen-Listbox.

## Hinweise

- **Systemschutz**: Das Tool blockiert automatisch kritische Systempfade (C:\, C:\Windows, C:\Program Files)
- **Logfile**: Alle Verschiebe-Aktionen werden in `NichtUploadfaehig_Log_YYYYMMDD_HHMMSS.txt` im Zielordner dokumentiert
- **Pakete**: Gültige Dateien werden automatisch in Upload-Pakete ≤ 1 GiB eingeteilt
- **Große Ordner**: Ordner > 1 GiB werden rekursiv auf Unterebenen aufgeteilt
