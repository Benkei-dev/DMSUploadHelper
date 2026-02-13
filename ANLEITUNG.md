# Schnellstart-Anleitung

## Auf einem anderen Rechner verwenden

### 1. EXE herunterladen

**Download:** [DMS-Upload-Vorbereitung.exe (v1.0)](https://github.com/Benkei-dev/DMSUploadHelper/releases/latest)

Die fertige EXE kann direkt ausgeführt werden – **keine Installation nötig, kein Python nötig**.

### 2. Tool starten

Einfach Doppelklick auf die EXE → das GUI-Fenster öffnet sich.

### 2. Tool starten

Einfach Doppelklick auf die EXE → das GUI-Fenster öffnet sich.

### 3. Verwendung
1. **Quellordner auswählen** – Der Ordner, dessen Dateien analysiert werden sollen
2. **Zielbasis auswählen** (optional) – Wohin nicht-uploadfähige Dateien verschoben werden. Standard: `_NichtUploadfaehig` im Quellordner
3. **Trockenlauf** aktivieren für eine Vorschau ohne Dateioperationen
4. **Analyse starten** klicken

---

## Für Entwickler: EXE selbst bauen

Falls du die EXE selbst erstellen oder den Code anpassen willst, brauchst du **Python 3.10+**.

```bash
# Repository klonen
git clone https://github.com/Benkei-dev/DMSUploadHelper.git
cd DMSUploadHelper

# Direkt starten (zum Testen)
python main.py

# EXE bauen
pip install pyinstaller
pyinstaller --onefile --windowed --name "DMS-Upload-Vorbereitung" main.py
```

Die fertige EXE liegt dann in `dist/DMS-Upload-Vorbereitung.exe`.

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
