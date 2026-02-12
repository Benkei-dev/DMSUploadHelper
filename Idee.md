"""
AUFGABE FÜR CODEX:

Programmiere ein Python-Tool mit GUI (tkinter), das Benutzer bei der Vorbereitung eines Uploads
in ein DMS (Fabasoft) unterstützt. Das Tool soll später mit PyInstaller zu einer EXE gebaut
werden können und ohne zusätzliche Installation beim User laufen (nur Standardbibliothek).

ZIELE:
1. Benutzer wählen einen Quellordner (Datenordner, NICHT Systempfad).
2. Das Tool findet alle nicht-uploadfähigen Dateien (konfigurierbare Liste von Dateiendungen) und
   verschiebt sie in einen zentralen Zielbasis-Ordner, wobei die ursprüngliche Ordnerstruktur
   unterhalb dieser Zielbasis gespiegelt wird (Variante A).
3. Die verbleibenden, gültigen Dateien werden für Uploads in Pakete von maximal 1 GiB eingeteilt.
   Wenn ein Ordner > 1 GiB ist, wird automatisch auf der nächsttieferen Ebene weiter unterteilt.
   Wenn einzelne Dateien > 1 GiB sind, wird das als Problem gemeldet.
4. Alle Verschiebe-Aktionen (oder geplanten Verschiebe-Aktionen im Trockenlauf) werden in
   einem Logfile (Text/CSV) dokumentiert.
5. Upload-Paketvorschläge werden im GUI-Textbereich angezeigt (kein zusätzlicher Report als Datei).
6. Die Liste der nicht-uploadfähigen Dateiendungen kann in der GUI bearbeitet und in einer
   JSON-Konfigurationsdatei gespeichert werden, die neben dem Programm liegt.

RAHMENBEDINGUNGEN:
- Programmiersprache: Python 3
- Nur Standardbibliothek verwenden (tkinter, pathlib, os, shutil, json, datetime, etc.).
- Keine externen Abhängigkeiten.
- Code so schreiben, dass eine spätere Umwandlung mit PyInstaller möglich ist, z. B.:
  pyinstaller --onefile --windowed main.py
- Variablen- und Funktionsnamen dürfen deutsch und sprechend sein.

KONFIGURATION / KONSTANTEN:
- MAX_PAKET_GROESSE = 1 * 1024 * 1024 * 1024  # 1 GiB in Bytes
- DEFAULT_UNGUELTIGE_ENDUNGEN = {
    ".exe", ".bat", ".cmd", ".com",
    ".ps1", ".psm1", ".vbs", ".js",
    ".msi", ".msp", ".lnk"
  }
  - Diese Default-Liste wird nur verwendet, wenn keine Konfigurationsdatei vorhanden ist.
  - Endungsprüfung soll case-insensitive erfolgen (alles auf lower()).
- Konfigurationsdatei:
  - Name: "dms_vorbereitung_config.json"
  - Speicherort: im selben Verzeichnis wie das Skript bzw. die EXE.
  - Struktur (JSON):

    {
      "ungueltige_endungen": [
        ".exe",
        ".bat",
        ".cmd",
        ...
      ]
    }

- Beim Start:
  - Ermittele das Verzeichnis des laufenden Programms (bei EXE: Ordner der EXE).
  - Wenn "dms_vorbereitung_config.json" existiert:
    - JSON laden und `ungueltige_endungen` als Set[str] verwenden (lowercased).
  - Wenn nicht:
    - DEFAULT_UNGUELTIGE_ENDUNGEN verwenden.

SYSTEMSCHUTZ:
- Quellordner darf NICHT "C:\\" sein.
- Quellordner darf NICHT direkt unter oder innerhalb von:
  - "C:\\Windows"
  - "C:\\Program Files"
  - "C:\\Program Files (x86)"
  liegen.
- Wenn ein solcher Pfad gewählt wird, eine verständliche Fehlermeldung per Messagebox anzeigen
  und nicht weiter verarbeiten.

GUI-ANFORDERUNGEN (tkinter):
Hauptfenster mit mindestens:

1. Erklärung
   - Ein Label mit einer kurzen Beschreibung, was das Tool macht.

2. Bereich "Quellordner"
   - Readonly-Textfeld zur Anzeige des ausgewählten Quellpfads.
   - Button "Quellordner auswählen..." -> Öffnet Ordnerdialog (tkinter.filedialog.askdirectory).

3. Bereich "Zielbasis (Nicht uploadfähig)"
   - Readonly-Textfeld zur Anzeige des Zielbasis-Ordners für nicht-uploadfähige Dateien.
   - Button "Zielordner auswählen..." -> Öffnet Ordnerdialog.
   - Verhalten:
     - Wenn der User KEINEN Zielordner auswählt, wird standardmäßig unterhalb des Quellordners
       ein Ordner "_NichtUploadfaehig" angelegt und als Zielbasis verwendet.

4. Bereich "Nicht-uploadfähige Dateiendungen" (Konfiguration)
   - Überschrift: "Nicht uploadfähige Dateiendungen"
   - Listbox oder ähnliche Anzeige, in der die aktuell verwendeten Endungen angezeigt werden
     (z. B. ".exe", ".bat", ".cmd", ...).
   - Eingabefeld für eine neue Endung:
     - User kann z. B. "mp4" oder ".mp4" eingeben.
     - Bei Hinzufügen:
       - Eingabe trimmen, auf lower() setzen.
       - Falls kein führender Punkt vorhanden ist, einen Punkt ergänzen.
       - Nur hinzufügen, wenn noch nicht in der Liste.
   - Buttons:
     - "Endung hinzufügen" -> fügt den Inhalt des Eingabefelds zur Liste hinzu.
     - "Markierte Endung entfernen" -> entfernt die Auswahl aus der Listbox.
     - "Endungen speichern" -> schreibt die aktuelle Liste als JSON in
       "dms_vorbereitung_config.json" im Programmverzeichnis.
   - Beim Laden des Programms:
     - Konfiguration laden (falls vorhanden) und die Endungen in der Listbox anzeigen.
     - Bei Fehlern (kaputtes JSON) eine sinnvolle Default-Liste verwenden und einen Hinweis
       im GUI-Textbereich ausgeben.

5. Checkbox "Trockenlauf (nur prüfen, nichts verschieben)"
   - Wenn aktiviert:
     - Dateien werden NICHT physisch verschoben.
     - Die Logik (Pakete, Größenberechnungen) läuft so, als wären die ungültigen Dateien entfernt.
     - Im Log wird Aktion = "wuerde_verschieben" verwendet.

6. Button "Analyse starten"
   - Startet den gesamten Prozess:
     - Eingaben prüfen.
     - Quellordner scannen.
     - Ungültige Dateien verarbeiten (verschieben oder simulieren).
     - Logfile schreiben.
     - Upload-Pakete berechnen.
     - Textausgabe im GUI aktualisieren.

7. Textbereich (tkinter.Text oder ScrolledText)
   - Anzeige von:
     - Kurzer Zusammenfassung (Quellordner, Zielbasis).
     - Anzahl ungültiger Dateien.
     - Pfad zum Logfile.
     - Paketvorschläge pro Ebene.
     - Warnungen (z. B. Dateien > 1 GiB).

8. Status-Label
   - Ein einfaches Label mit kurzen Statusmeldungen:
     - "Bereit"
     - "Scanne Ordner..."
     - "Verschiebe ungueltige Dateien..."
     - "Berechne Upload-Pakete..."
     - "Fertig" oder "Fehler: ..."

VERARBEITUNGSLOGIK – DETAILS:

1. Eingaben prüfen:
   - Wenn kein Quellordner ausgewählt -> Messagebox-Fehler.
   - Wenn Quellordner ein verbotener Systempfad ist -> Messagebox-Fehler.
   - Wenn kein Zielbasis-Ordner ausgewählt:
     - Zielbasis = Quellordner / "_NichtUploadfaehig".

2. Quellordner scannen:
   - Rekursiv mit os.walk oder pathlib durch den Quellordner.
   - Den Zielbasis-Ordner und seine Unterordner beim Scan ignorieren (keine Selbstverarbeitung).
   - Jede gefundene Datei:
     - Suffix = lowercased Endung (`Path.suffix.lower()`).
     - Dateigröße in Bytes ermitteln.
     - In zwei Kategorien einteilen:
       - ungültige Datei (Endung in ungueltige_endungen-Set)
       - gültige Datei (alle anderen)
   - Informationen in Datenstrukturen sammeln, die später für:
     - Verschiebe-Logik,
     - Paketbildung,
     - Ausgabetext
     benötigt werden.

3. Umgang mit nicht-uploadfähigen Dateien (Variante A, zentrales Ziel mit gespiegelter Struktur):
   - Zielbasis-Ordner ist vom User gewählt oder Standard (Quellordner/_NichtUploadfaehig).
   - Für jede ungültige Datei:
     - Berechne relativen Pfad bezogen auf den Quellordner.
     - Beispiel:
       - Quellordner: "U:\\FB51"
       - Datei: "U:\\FB51\\Projekte\\Kita\\Alt\\notiz.tmp"
       - Relativpfad: "Projekte\\Kita\\Alt\\notiz.tmp"
     - Zielpfad:
       - Zielbasis / <Name des Quellwurzelordners oder Laufwerksbuchstaben> / relativer Pfad
       - Beispiel:
         - Zielbasis: "U:\\_NichtUploadfaehig_Gesamt"
         - Quellwurzelname: "FB51"
         - Zielpfad: "U:\\_NichtUploadfaehig_Gesamt\\FB51\\Projekte\\Kita\\Alt\\notiz.tmp"
     - Zielordnerstruktur mit mkdir(..., parents=True, exist_ok=True) erzeugen.
     - Wenn Trockenlauf == False:
       - Datei mit shutil.move(...) verschieben.
     - Wenn Trockenlauf == True:
       - Datei NICHT verschieben, aber so behandeln, als wäre sie entfernt (für Paketberechnung ignorieren).

4. Logfile:
   - Pro Programmlauf ein neues Logfile.
   - Speicherort: Zielbasis-Ordner.
   - Dateiname: "NichtUploadfaehig_Log_YYYYMMDD_HHMMSS.txt"
     - mit datetime.now().strftime("%Y%m%d_%H%M%S")
   - Format: UTF-8-Textdatei, erste Zeile (Header):

     DatumZeit;Aktion;Grund;OriginalPfad;NeuerPfad;DateigroesseBytes

   - Für jede ungültige Datei eine Zeile:
     - DatumZeit: z. B. "2025-11-19 18:30:12"
     - Aktion:
       - "verschoben" bei erfolgreichem Move (Trockenlauf False).
       - "wuerde_verschieben" bei Trockenlauf True.
       - "fehler" bei Exception.
     - Grund:
       - z. B. "ungueltige_endung:.tmp" oder Exception-Text bei Fehler.
     - OriginalPfad: vollständiger Ursprungspfad.
     - NeuerPfad:
       - Zielpfad bei "verschoben" oder "wuerde_verschieben".
       - "-" oder leer bei "fehler", wenn kein Zielpfad zustande kam.
     - DateigroesseBytes: Dateigröße in Bytes.
   - Fehler beim Schreiben des Logfiles im GUI-Textbereich anzeigen, Programm soll aber nicht abstürzen.

5. Bildung der Upload-Pakete (<= 1 GiB):

   GRUNDIDEE:
   - Nur gültige Dateien betrachten (ungültige wurden schon verschoben oder logisch entfernt).
   - Für jede Ordner-Ebene Paketvorschläge machen.
   - Wenn ein Ordner > 1 GiB Gesamtgröße hat, in den Ordner „hineinspringen“ und auf der dortigen
     Ebene erneut Pakete bilden (rekursiv).
   - Einzeldateien > 1 GiB als Problem melden.

   SCHRITTE:

   5.1 Ordnergrößen berechnen
   - Für jede Datei wissen wir:
     - Pfad
     - Größe
   - Berechne:
     - Für jeden Ordner die Summe der Größen aller gültigen Dateien unterhalb dieses Ordners
       (inklusive Unterordnern).

   5.2 Paketbildung auf Ebene eines Ordners D
   - Für Ordner D:
     - Ermittle:
       - Liste der direkten Unterordner von D.
       - Liste der Dateien, die direkt in D liegen (ohne Unterordner).
   - Dateien direkt in D:
     - Summe der Dateigrößen berechnen.
     - Wenn Summe <= MAX_PAKET_GROESSE:
       - Behandle sie als eine "Pseudo-Einheit" mit einem Namen wie "[Dateien in diesem Ordner]".
     - Wenn Summe > MAX_PAKET_GROESSE:
       - Auf Dateiebene in Pakete aufteilen:
         - Dateien nach Name oder Größe sortieren.
         - Nacheinander in Pakete füllen, jeweils bis MAX_PAKET_GROESSE.
         - Wenn eine einzelne Datei > MAX_PAKET_GROESSE:
           - Diese Datei als Warnung markieren ("Datei > 1 GiB").
   - Unterordner von D:
     - Für jeden Unterordner U:
       - Gesamtgröße(U) betrachten.
       - Wenn Gesamtgröße(U) <= MAX_PAKET_GROESSE:
         - U kann als Einheit in Pakete aufgenommen werden.
       - Wenn Gesamtgröße(U) > MAX_PAKET_GROESSE:
         - Dieser Ordner wird NICHT direkt in Pakete von D aufgenommen.
         - Stattdessen:
           - Im Ergebnis für Ebene D vermerken, dass U zu groß ist.
           - Rekursiv die Paketbildung für U auf seiner Ebene durchführen (erstelle eigene Paketliste für diesen Ordner).
   - Paket-Bildung selbst:
     - Erzeuge eine Liste von Einheiten (Unterordner <= 1 GiB + evtl. Pseudo-Einheit für Dateien im Ordner).
     - Sortiere diese Einheiten z. B. nach Name.
     - Erzeuge leere Paketliste.
     - Für jede Einheit:
       - Wenn aktuelle Paketgröße + Einheitengröße <= MAX_PAKET_GROESSE:
         - Einheit in das aktuelle Paket aufnehmen.
       - Sonst:
         - aktuelles Paket abschließen, neues Paket starten, Einheit dort einfügen.
   - Ergebnis für Ordner D:
     - Liste von Paketen mit Namen der enthaltenen Einheiten und Gesamtgröße.
     - Liste von Unterordnern, die zu groß sind und rekursiv behandelt werden.

6. Ausgabe im GUI-Textbereich:
- Nachdem alles fertig ist:
  - Den Textbereich leeren.
  - Eine Zusammenfassung schreiben, z. B.:

    Analyse für Quellordner: U:\\FB51
    Zielbasis (nicht uploadfähige Dateien): U:\\_NichtUploadfaehig_Gesamt

    Nicht-uploadfähige Dateien:
      - Anzahl: 12
      - Details siehe Logfile:
        U:\\_NichtUploadfaehig_Gesamt\\NichtUploadfaehig_Log_20251119_183012.txt
      - Modus: Trockenlauf = Nein (oder Ja)

    Upload-Pakete auf Ebene: U:\\FB51
    ---------------------------------
    Paket 1 (0,82 GB):
      - Ordner: Projekte (0,45 GB)
      - Ordner: Scans (0,37 GB)

    Paket 2 (0,60 GB):
      - [Dateien in diesem Ordner] (0,60 GB)

    Ordner mit Unterteilung aufgrund > 1 GiB:
      - Ordner: Altbestand (1,34 GB) -> eigene Paketvorschläge auf Unterordner-Ebene

    Upload-Pakete für Ordner: U:\\FB51\\Altbestand
    ----------------------------------------------
    Paket 1 (0,90 GB):
      - Ordner: 2019 (0,50 GB)
      - Ordner: 2020 (0,40 GB)
    Paket 2 (0,44 GB):
      - Ordner: 2021 (0,44 GB)

    WARNUNGEN:
      - Datei U:\\FB51\\Altbestand\\2018\\Archiv.iso (1,20 GB) ist größer als 1 GiB und kann so
        nicht in einem Upload übertragen werden.

- Es reicht, wenn der Text sauber formatiert und lesbar ist; keine externe Report-Datei nötig
  (nur das Logfile für Verschiebeaktionen).

7. Funktionsstruktur (Vorschlag):
- Implementiere den Code möglichst modular, z. B.:

  - `lade_konfiguration()`:
    - Liest "dms_vorbereitung_config.json" aus dem Programmverzeichnis (falls vorhanden).
    - Gibt ein Set von Endungen zurück.
    - Bei Fehlern: Default-Set verwenden.

  - `speichere_konfiguration(ungueltige_endungen: set[str])`:
    - Schreibt die Endungen in "dms_vorbereitung_config.json" im Programmverzeichnis.

  - `scanne_quellordner(quellpfad: Path, zielbasis: Path, ungueltige_endungen: set[str], trockenlauf: bool) -> dict`:
    - Führt den Scan durch, verschiebt (oder simuliert) ungültige Dateien, schreibt das Logfile.
    - Gibt Datenstruktur zurück mit Infos über gültige Dateien und ggf. Warnungen.

  - `berechne_ordnergroessen(...) -> dict`:
    - Berechnet Gesamtgrößen pro Ordner.

  - `erstelle_paketvorschlaege(...) -> struktur`:
    - Führt die oben beschriebene Paketlogik aus.

  - `erstelle_ausgabetext(...) -> str`:
    - Baut den finalen Text für das GUI.

  - `class DMSVorbereitungApp(tk.Tk): ...`:
    - Enthält das tkinter-Fenster, GUI-Elemente, Events und Aufrufe der oben genannten Funktionen.

Bitte nun den vollständigen Python-Code erstellen, der diese Anforderungen umsetzt.
"""
