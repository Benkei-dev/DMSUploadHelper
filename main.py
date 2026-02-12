#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMS Upload-Vorbereitung (Fabasoft)
===================================
Tkinter-GUI-Tool, das Benutzer bei der Vorbereitung eines Uploads
in ein DMS (Fabasoft) unterstützt.

- Verschiebt nicht-uploadfähige Dateien in einen Zielordner (gespiegelte Struktur).
- Teilt gültige Dateien in Upload-Pakete ≤ 1 GiB ein.
- Logfile im CSV-Format.
- Trockenlauf-Modus.

Nur Python-Standardbibliothek – keine externen Abhängigkeiten.
"""

import json
import os
import shutil
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
MAX_PAKET_GROESSE: int = 1 * 1024 * 1024 * 1024  # 1 GiB

DEFAULT_UNGUELTIGE_ENDUNGEN: set[str] = {
    ".exe", ".bat", ".cmd", ".com",
    ".ps1", ".psm1", ".vbs", ".js",
    ".msi", ".msp", ".lnk",
}

KONFIG_DATEINAME = "dms_vorbereitung_config.json"

VERBOTENE_PFADE = [
    os.path.normcase(r"C:\\"),
    os.path.normcase(r"C:\Windows"),
    os.path.normcase(r"C:\Program Files"),
    os.path.normcase(r"C:\Program Files (x86)"),
]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def programmverzeichnis() -> Path:
    """Gibt das Verzeichnis zurück, in dem das Programm (oder die EXE) liegt."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def lade_konfiguration() -> set[str]:
    """Lädt die Liste ungültiger Endungen aus der JSON-Konfigurationsdatei."""
    konfig_pfad = programmverzeichnis() / KONFIG_DATEINAME
    try:
        if konfig_pfad.exists():
            with open(konfig_pfad, "r", encoding="utf-8") as f:
                daten = json.load(f)
            endungen = {e.lower() for e in daten.get("ungueltige_endungen", [])}
            if endungen:
                return endungen
    except (json.JSONDecodeError, OSError):
        pass
    return set(DEFAULT_UNGUELTIGE_ENDUNGEN)


def speichere_konfiguration(ungueltige_endungen: set[str]) -> None:
    """Schreibt die Endungen als JSON in die Konfigurationsdatei."""
    konfig_pfad = programmverzeichnis() / KONFIG_DATEINAME
    daten = {"ungueltige_endungen": sorted(ungueltige_endungen)}
    with open(konfig_pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)


def ist_verbotener_pfad(pfad: Path) -> bool:
    """Prüft, ob der Pfad ein geschützter Systempfad ist."""
    norm = os.path.normcase(str(pfad.resolve()))
    for verboten in VERBOTENE_PFADE:
        if norm == verboten or norm.startswith(verboten + os.sep):
            return True
    # Direkt C:\ ohne Unterordner
    if len(norm) <= 3 and norm.endswith(("\\", "/")):
        return True
    return False


# ---------------------------------------------------------------------------
# Scan & Verschieben
# ---------------------------------------------------------------------------

def scanne_quellordner(
    quellpfad: Path,
    zielbasis: Path,
    ungueltige_endungen: set[str],
    trockenlauf: bool,
) -> dict:
    """
    Scannt den Quellordner rekursiv.
    Verschiebt (oder simuliert) ungültige Dateien und sammelt gültige Dateien.
    Schreibt ein Logfile.

    Rückgabe: dict mit Schlüsseln:
        - gueltige_dateien: list[(Path, int)]   (Pfad, Größe)
        - anzahl_ungueltig: int
        - logdatei: Path | None
        - fehler: list[str]
    """
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    logdatei = zielbasis / f"NichtUploadfaehig_Log_{zeitstempel}.txt"
    quellwurzelname = quellpfad.name or quellpfad.anchor.replace("\\", "").replace(":", "")

    gueltige_dateien: list[tuple[Path, int]] = []
    log_zeilen: list[str] = []
    fehler: list[str] = []
    anzahl_ungueltig = 0

    header = "DatumZeit;Aktion;Grund;OriginalPfad;NeuerPfad;DateigroesseBytes"
    log_zeilen.append(header)

    for verz, _, dateien in os.walk(quellpfad):
        verz_pfad = Path(verz)

        # Zielbasis-Ordner beim Scan ignorieren
        try:
            verz_pfad.relative_to(zielbasis)
            continue  # Liegt innerhalb der Zielbasis → überspringen
        except ValueError:
            pass

        for dateiname in dateien:
            datei = verz_pfad / dateiname
            try:
                groesse = datei.stat().st_size
            except OSError:
                groesse = 0

            endung = datei.suffix.lower()

            if endung in ungueltige_endungen:
                anzahl_ungueltig += 1
                relativ = datei.relative_to(quellpfad)
                zielpfad = zielbasis / quellwurzelname / relativ
                jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if trockenlauf:
                    aktion = "wuerde_verschieben"
                    log_zeilen.append(
                        f"{jetzt};{aktion};ungueltige_endung:{endung};"
                        f"{datei};{zielpfad};{groesse}"
                    )
                else:
                    try:
                        zielpfad.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(datei), str(zielpfad))
                        aktion = "verschoben"
                        log_zeilen.append(
                            f"{jetzt};{aktion};ungueltige_endung:{endung};"
                            f"{datei};{zielpfad};{groesse}"
                        )
                    except Exception as ex:
                        aktion = "fehler"
                        fehler.append(f"{datei}: {ex}")
                        log_zeilen.append(
                            f"{jetzt};{aktion};{ex};{datei};-;{groesse}"
                        )
            else:
                gueltige_dateien.append((datei, groesse))

    # Logfile schreiben
    try:
        zielbasis.mkdir(parents=True, exist_ok=True)
        with open(logdatei, "w", encoding="utf-8") as f:
            f.write("\n".join(log_zeilen) + "\n")
    except OSError as ex:
        fehler.append(f"Logfile konnte nicht geschrieben werden: {ex}")
        logdatei = None

    return {
        "gueltige_dateien": gueltige_dateien,
        "anzahl_ungueltig": anzahl_ungueltig,
        "logdatei": logdatei,
        "fehler": fehler,
    }


# ---------------------------------------------------------------------------
# Paketbildung
# ---------------------------------------------------------------------------

def berechne_ordnergroessen(gueltige_dateien: list[tuple[Path, int]]) -> dict[Path, int]:
    """Berechnet die Gesamtgröße pro Ordner (rekursiv)."""
    groessen: dict[Path, int] = {}
    for datei, groesse in gueltige_dateien:
        ordner = datei.parent
        while True:
            groessen[ordner] = groessen.get(ordner, 0) + groesse
            eltern = ordner.parent
            if eltern == ordner:
                break
            ordner = eltern
    return groessen


def erstelle_paketvorschlaege(
    ordner: Path,
    gueltige_dateien: list[tuple[Path, int]],
    ordnergroessen: dict[Path, int],
    max_groesse: int = MAX_PAKET_GROESSE,
) -> list[dict]:
    """
    Erstellt rekursive Paketvorschläge für einen Ordner.

    Rückgabe: Liste von Einträgen mit:
        - ordner: Path
        - pakete: list[list[(str, int)]]
        - warnungen: list[str]
        - unterordner_aufgeteilt: list[Path]  (rekursiv behandelt)
    """
    ergebnisse: list[dict] = []
    _paketbildung_rekursiv(ordner, gueltige_dateien, ordnergroessen, max_groesse, ergebnisse)
    return ergebnisse


def _paketbildung_rekursiv(
    ordner: Path,
    alle_dateien: list[tuple[Path, int]],
    ordnergroessen: dict[Path, int],
    max_groesse: int,
    ergebnisse: list[dict],
) -> None:
    """Rekursive Paketbildung für einen Ordner."""
    # Direkte Unterordner
    unterordner: set[Path] = set()
    dateien_im_ordner: list[tuple[Path, int]] = []

    for datei, groesse in alle_dateien:
        if datei.parent == ordner:
            dateien_im_ordner.append((datei, groesse))
        else:
            try:
                rel = datei.relative_to(ordner)
                erster_teil = ordner / rel.parts[0]
                if erster_teil.is_dir():
                    unterordner.add(erster_teil)
            except ValueError:
                pass

    # Einheiten sammeln
    einheiten: list[tuple[str, int]] = []
    warnungen: list[str] = []
    zu_gross: list[Path] = []

    # Dateien direkt im Ordner
    summe_dateien = sum(g for _, g in dateien_im_ordner)
    if summe_dateien > 0:
        if summe_dateien <= max_groesse:
            einheiten.append(("[Dateien in diesem Ordner]", summe_dateien))
        else:
            # Auf Dateiebene aufteilen
            dateien_im_ordner.sort(key=lambda x: x[0].name)
            paket: list[tuple[str, int]] = []
            paket_groesse = 0
            for datei, groesse in dateien_im_ordner:
                if groesse > max_groesse:
                    warnungen.append(
                        f"Datei {datei} ({_formatiere_groesse(groesse)}) "
                        f"ist größer als 1 GiB!"
                    )
                    continue
                if paket_groesse + groesse > max_groesse:
                    einheiten.append(
                        (f"[Dateien-Paket: {len(paket)} Dateien]", paket_groesse)
                    )
                    paket = []
                    paket_groesse = 0
                paket.append((datei.name, groesse))
                paket_groesse += groesse
            if paket:
                einheiten.append(
                    (f"[Dateien-Paket: {len(paket)} Dateien]", paket_groesse)
                )

    # Unterordner
    for uo in sorted(unterordner):
        uo_groesse = ordnergroessen.get(uo, 0)
        if uo_groesse == 0:
            continue
        if uo_groesse <= max_groesse:
            einheiten.append((f"Ordner: {uo.name}", uo_groesse))
        else:
            zu_gross.append(uo)

    # Pakete bilden aus Einheiten
    einheiten.sort(key=lambda x: x[0])
    pakete: list[list[tuple[str, int]]] = []
    aktuelles_paket: list[tuple[str, int]] = []
    aktuelle_groesse = 0

    for name, groesse in einheiten:
        if aktuelle_groesse + groesse > max_groesse and aktuelles_paket:
            pakete.append(aktuelles_paket)
            aktuelles_paket = []
            aktuelle_groesse = 0
        aktuelles_paket.append((name, groesse))
        aktuelle_groesse += groesse

    if aktuelles_paket:
        pakete.append(aktuelles_paket)

    ergebnisse.append({
        "ordner": ordner,
        "pakete": pakete,
        "warnungen": warnungen,
        "unterordner_aufgeteilt": zu_gross,
    })

    # Rekursiv für zu große Unterordner
    for uo in sorted(zu_gross):
        uo_dateien = [(d, g) for d, g in alle_dateien
                      if str(d).startswith(str(uo) + os.sep) or d.parent == uo]
        _paketbildung_rekursiv(uo, uo_dateien, ordnergroessen, max_groesse, ergebnisse)


def _formatiere_groesse(bytes_wert: int) -> str:
    """Formatiert Bytes als lesbare Größe."""
    if bytes_wert >= 1024 * 1024 * 1024:
        return f"{bytes_wert / (1024**3):.2f} GB"
    if bytes_wert >= 1024 * 1024:
        return f"{bytes_wert / (1024**2):.2f} MB"
    if bytes_wert >= 1024:
        return f"{bytes_wert / 1024:.2f} KB"
    return f"{bytes_wert} Bytes"


# ---------------------------------------------------------------------------
# Ausgabetext
# ---------------------------------------------------------------------------

def erstelle_ausgabetext(
    quellpfad: Path,
    zielbasis: Path,
    trockenlauf: bool,
    scan_ergebnis: dict,
    paketvorschlaege: list[dict],
) -> str:
    """Baut den finalen Text für das GUI."""
    zeilen: list[str] = []
    zeilen.append(f"Analyse für Quellordner: {quellpfad}")
    zeilen.append(f"Zielbasis (nicht uploadfähige Dateien): {zielbasis}")
    zeilen.append("")

    modus = "Ja" if trockenlauf else "Nein"
    zeilen.append(f"Trockenlauf: {modus}")
    zeilen.append("")

    zeilen.append("Nicht-uploadfähige Dateien:")
    zeilen.append(f"  Anzahl: {scan_ergebnis['anzahl_ungueltig']}")
    if scan_ergebnis["logdatei"]:
        zeilen.append(f"  Logfile: {scan_ergebnis['logdatei']}")
    zeilen.append("")

    # Paketvorschläge
    for eintrag in paketvorschlaege:
        ordner = eintrag["ordner"]
        pakete = eintrag["pakete"]
        warnungen = eintrag["warnungen"]
        zu_gross = eintrag["unterordner_aufgeteilt"]

        zeilen.append(f"Upload-Pakete auf Ebene: {ordner}")
        zeilen.append("-" * 50)

        if not pakete and not zu_gross:
            zeilen.append("  (keine gültigen Dateien auf dieser Ebene)")
        else:
            for i, paket in enumerate(pakete, 1):
                gesamt = sum(g for _, g in paket)
                zeilen.append(f"  Paket {i} ({_formatiere_groesse(gesamt)}):")
                for name, groesse in paket:
                    zeilen.append(f"    - {name} ({_formatiere_groesse(groesse)})")

        if zu_gross:
            zeilen.append("")
            zeilen.append("  Ordner mit Unterteilung aufgrund > 1 GiB:")
            for uo in zu_gross:
                zeilen.append(f"    - {uo.name} -> eigene Paketvorschläge unten")

        if warnungen:
            zeilen.append("")
            zeilen.append("  WARNUNGEN:")
            for w in warnungen:
                zeilen.append(f"    ⚠ {w}")

        zeilen.append("")

    # Fehler
    if scan_ergebnis["fehler"]:
        zeilen.append("FEHLER:")
        for f in scan_ergebnis["fehler"]:
            zeilen.append(f"  ✗ {f}")

    return "\n".join(zeilen)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class DMSVorbereitungApp(tk.Tk):
    """Hauptfenster der DMS-Upload-Vorbereitung."""

    def __init__(self) -> None:
        super().__init__()
        self.title("DMS Upload-Vorbereitung (Fabasoft)")
        self.geometry("900x750")
        self.minsize(700, 600)

        self.ungueltige_endungen: set[str] = lade_konfiguration()
        self.quellpfad: Path | None = None
        self.zielbasis: Path | None = None

        self._erstelle_gui()
        self._aktualisiere_endungen_listbox()
        self._setze_status("Bereit")

    # ----- GUI-Aufbau -----

    def _erstelle_gui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # --- Erklärung ---
        erklaerung = (
            "Dieses Tool unterstützt Sie bei der Vorbereitung eines Uploads in "
            "ein DMS (Fabasoft).\nNicht-uploadfähige Dateien werden verschoben, "
            "gültige Dateien in Pakete ≤ 1 GiB eingeteilt."
        )
        tk.Label(self, text=erklaerung, justify="left", wraplength=850,
                 font=("Segoe UI", 10)).pack(anchor="w", **pad)

        tk.Frame(self, height=2, bd=1, relief="sunken").pack(fill="x", **pad)

        # --- Quellordner ---
        frame_quelle = tk.LabelFrame(self, text="Quellordner")
        frame_quelle.pack(fill="x", **pad)

        self.var_quellpfad = tk.StringVar(value="(nicht ausgewählt)")
        tk.Entry(frame_quelle, textvariable=self.var_quellpfad,
                 state="readonly", width=80).pack(side="left", padx=4, pady=4, expand=True, fill="x")
        tk.Button(frame_quelle, text="Quellordner auswählen…",
                  command=self._waehle_quellordner).pack(side="right", padx=4)

        # --- Zielbasis ---
        frame_ziel = tk.LabelFrame(self, text="Zielbasis (nicht uploadfähige Dateien)")
        frame_ziel.pack(fill="x", **pad)

        self.var_zielbasis = tk.StringVar(value="(Standard: _NichtUploadfaehig im Quellordner)")
        tk.Entry(frame_ziel, textvariable=self.var_zielbasis,
                 state="readonly", width=80).pack(side="left", padx=4, pady=4, expand=True, fill="x")
        tk.Button(frame_ziel, text="Zielordner auswählen…",
                  command=self._waehle_zielbasis).pack(side="right", padx=4)

        # --- Endungen ---
        frame_endungen = tk.LabelFrame(self, text="Nicht uploadfähige Dateiendungen")
        frame_endungen.pack(fill="x", **pad)

        self.listbox_endungen = tk.Listbox(frame_endungen, height=5, width=20,
                                           selectmode="single", exportselection=False)
        self.listbox_endungen.pack(side="left", padx=4, pady=4)

        frame_end_buttons = tk.Frame(frame_endungen)
        frame_end_buttons.pack(side="left", padx=4)

        self.var_neue_endung = tk.StringVar()
        tk.Entry(frame_end_buttons, textvariable=self.var_neue_endung,
                 width=12).pack(pady=2)
        tk.Button(frame_end_buttons, text="Endung hinzufügen",
                  command=self._endung_hinzufuegen).pack(fill="x", pady=2)
        tk.Button(frame_end_buttons, text="Markierte entfernen",
                  command=self._endung_entfernen).pack(fill="x", pady=2)
        tk.Button(frame_end_buttons, text="Endungen speichern",
                  command=self._endungen_speichern).pack(fill="x", pady=2)

        # --- Trockenlauf + Start ---
        frame_aktion = tk.Frame(self)
        frame_aktion.pack(fill="x", **pad)

        self.var_trockenlauf = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_aktion, text="Trockenlauf (nur prüfen, nichts verschieben)",
                       variable=self.var_trockenlauf).pack(side="left", padx=4)

        tk.Button(frame_aktion, text="▶  Analyse starten", font=("Segoe UI", 10, "bold"),
                  bg="#4CAF50", fg="white",
                  command=self._analyse_starten).pack(side="right", padx=4)

        # --- Textbereich ---
        self.textbereich = scrolledtext.ScrolledText(self, wrap="word", height=18,
                                                     font=("Consolas", 9))
        self.textbereich.pack(fill="both", expand=True, **pad)

        # --- Status ---
        self.var_status = tk.StringVar(value="Bereit")
        tk.Label(self, textvariable=self.var_status, anchor="w",
                 relief="sunken", bd=1).pack(fill="x", side="bottom")

    # ----- Callbacks -----

    def _waehle_quellordner(self) -> None:
        pfad = filedialog.askdirectory(title="Quellordner auswählen")
        if pfad:
            self.quellpfad = Path(pfad)
            self.var_quellpfad.set(str(self.quellpfad))

    def _waehle_zielbasis(self) -> None:
        pfad = filedialog.askdirectory(title="Zielordner auswählen")
        if pfad:
            self.zielbasis = Path(pfad)
            self.var_zielbasis.set(str(self.zielbasis))

    def _endung_hinzufuegen(self) -> None:
        eingabe = self.var_neue_endung.get().strip().lower()
        if not eingabe:
            return
        if not eingabe.startswith("."):
            eingabe = "." + eingabe
        if eingabe in self.ungueltige_endungen:
            messagebox.showinfo("Info", f"'{eingabe}' ist bereits in der Liste.")
            return
        self.ungueltige_endungen.add(eingabe)
        self._aktualisiere_endungen_listbox()
        self.var_neue_endung.set("")

    def _endung_entfernen(self) -> None:
        auswahl = self.listbox_endungen.curselection()
        if not auswahl:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Endung auswählen.")
            return
        endung = self.listbox_endungen.get(auswahl[0])
        self.ungueltige_endungen.discard(endung)
        self._aktualisiere_endungen_listbox()

    def _endungen_speichern(self) -> None:
        try:
            speichere_konfiguration(self.ungueltige_endungen)
            messagebox.showinfo("Gespeichert",
                                f"Endungen gespeichert in:\n{programmverzeichnis() / KONFIG_DATEINAME}")
        except OSError as ex:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{ex}")

    def _aktualisiere_endungen_listbox(self) -> None:
        self.listbox_endungen.delete(0, tk.END)
        for endung in sorted(self.ungueltige_endungen):
            self.listbox_endungen.insert(tk.END, endung)

    def _setze_status(self, text: str) -> None:
        self.var_status.set(text)
        self.update_idletasks()

    def _analyse_starten(self) -> None:
        # Eingaben prüfen
        if not self.quellpfad:
            messagebox.showerror("Fehler", "Bitte zuerst einen Quellordner auswählen.")
            return
        if not self.quellpfad.exists():
            messagebox.showerror("Fehler", f"Der Quellordner existiert nicht:\n{self.quellpfad}")
            return
        if ist_verbotener_pfad(self.quellpfad):
            messagebox.showerror(
                "Systemschutz",
                "Der gewählte Quellordner ist ein geschützter Systempfad!\n\n"
                "Folgende Pfade sind nicht erlaubt:\n"
                "• C:\\\n• C:\\Windows\n• C:\\Program Files\n• C:\\Program Files (x86)"
            )
            return

        # Zielbasis
        if not self.zielbasis:
            self.zielbasis = self.quellpfad / "_NichtUploadfaehig"
            self.var_zielbasis.set(str(self.zielbasis))

        trockenlauf = self.var_trockenlauf.get()

        # Textbereich leeren
        self.textbereich.delete("1.0", tk.END)

        # 1. Scannen
        self._setze_status("Scanne Ordner…")
        scan_ergebnis = scanne_quellordner(
            self.quellpfad, self.zielbasis,
            self.ungueltige_endungen, trockenlauf,
        )

        # 2. Ordnergrößen berechnen
        self._setze_status("Berechne Upload-Pakete…")
        ordnergroessen = berechne_ordnergroessen(scan_ergebnis["gueltige_dateien"])

        # 3. Paketvorschläge
        paketvorschlaege = erstelle_paketvorschlaege(
            self.quellpfad,
            scan_ergebnis["gueltige_dateien"],
            ordnergroessen,
        )

        # 4. Ausgabetext
        text = erstelle_ausgabetext(
            self.quellpfad, self.zielbasis, trockenlauf,
            scan_ergebnis, paketvorschlaege,
        )
        self.textbereich.insert("1.0", text)

        self._setze_status("Fertig ✓")


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main() -> None:
    app = DMSVorbereitungApp()
    app.mainloop()


if __name__ == "__main__":
    main()
