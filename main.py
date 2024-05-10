import os
import sys
import subprocess
import serial
from reportlab.pdfgen import canvas
import time


# Funktion zum Einlesen der DUT-ID über die Kommandozeile
def get_dut_id():
    # Interaktive Aufforderung zur Eingabe der DUT-ID
    dut_id = input("Geben Sie die DUT-ID ein (z.B. BatXDev20240510): ")

    # Validierung der DUT-ID (optional)
    if not dut_id:
        raise ValueError("DUT-ID darf nicht leer sein.")

    return dut_id

# Funktion zum Starten der Testumgebung mit `testdata.py`
def start_test_environment(dut_id):
    # Pfad zu `testdata.py`
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    TESTDATA_PATH = os.path.join(SCRIPT_DIR, "testdata.py")

    # Überprüfen, ob `testdata.py` existiert
    if not os.path.exists(TESTDATA_PATH):
        raise FileNotFoundError(f"`testdata.py` nicht gefunden: {TESTDATA_PATH}")

    # Starten von `testdata.py` mit der DUT-ID als Argument
    subprocess.run([sys.executable, TESTDATA_PATH, dut_id], check=True)

# Funktion zum Lesen von Daten über die serielle Schnittstelle
def read_serial_data(serial_port):
    with serial.Serial(serial_port, 9600, timeout=1) as ser:
        data = []
        while ser.in_waiting:
            line = ser.readline().decode().strip()
            data.append(line)
        return data

# Funktion zum Prüfen der Messdaten
def check_measurements(data):
    voltage_range = (7.0, 10)  # Beispiel für Spannungsbereich
    current_range = (0, 20)  # Beispiel für Strombereich

    report = []
    for line in data:
        voltage, current = map(float, line.split())
        if not (voltage_range[0] <= voltage <= voltage_range[1]):
            report.append(f"Spannung außerhalb des Bereichs: {voltage}")
        if not (current_range[0] <= current <= current_range[1]):
            report.append(f"Strom außerhalb des Bereichs: {current}")

    return report  # Gibt die Liste der Probleme oder einen leeren Bericht zurück

# Funktion zur Erstellung eines Prüfprotokolls (PDF)
def create_report(dut_id, report_data):
    # Verzeichnis zum Speichern des Protokolls
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))  # Verzeichnis des Skripts
    REPORTS_DIR = os.path.join(SCRIPT_DIR, "Protokolle")  # Unterverzeichnis für Protokolle

    # Erstellen des Verzeichnisses, wenn es nicht existiert
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    # Dateiname und Pfad für das Protokoll
    report_path = os.path.join(REPORTS_DIR, f"{dut_id}_Pruefprotokoll.pdf")

    # Erstellen des PDF-Protokolls
    c = canvas.Canvas(report_path)

    c.drawString(100, 800, f"Prüfprotokoll für DUT-ID: {dut_id}")
    c.drawString(100, 780, "Prüfungsergebnisse:")
    
    y_position = 760
    for item in report_data:
        c.drawString(100, y_position, item)
        y_position -= 20

    c.showPage()
    c.save()

    print(f"Prüfprotokoll gespeichert unter: {report_path}")

# Hauptfunktion
def main():
    try:
        dut_id = get_dut_id()  # Eingabe der DUT-ID

        # Aufruf von `testdata.py`
        start_test_environment(dut_id)

        # Lesen der Daten von der seriellen Schnittstelle
        data = read_serial_data(serial_port)

        if not data:
            print("Keine Daten gefunden")
            return

        # Prüfen der Messdaten
        report = check_measurements(data)

        # Erstellung des Prüfprotokolls
        create_report(dut_id, report)

    except Exception as e:
        print(f"Fehler: {e}")

# Ausführen des Hauptprogramms
if __name__ == "__main__":
    main()