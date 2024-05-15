import os
import sys
import io
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime

class VirtualSerial(io.StringIO):
    def __init__(self):
        super().__init__()
        self.buffer = ""

    def write(self, data):
        super().write(data)
        self.buffer += data

    def readline(self):
        if self.buffer:
            line = self.buffer
            self.buffer = ""
            return line
        return ""

# DUT-ID Abfrage / Eingabe
def get_dut_id():
    dut_id = input("Geben Sie die DUT-ID ein (z.B. BatXDev20240510): ")
    if not dut_id:
        raise ValueError("DUT-ID darf nicht leer sein.")
    return dut_id

# Überprüfe ob Testdaten vorhanden sind
def start_test_environment(dut_id, serial_port):
    try:
        serial_port.write(dut_id + "\n")
        result = subprocess.run([sys.executable, "testdata.py", dut_id], capture_output=True, text=True)
        response = result.stdout.strip()
        serial_port.write(response + "\n")
        print(f"Antwort von testdata.py: {response}")
        if "does not exist" in response:
            raise FileNotFoundError(response)
    except Exception as e:
        print(f"Fehler bei der virtuellen seriellen Kommunikation: {e}")
        raise

# Lesen der seriellen Schnittstelle
def read_serial_data(serial_port):
    data = []
    try:
        while True:
            line = serial_port.readline().strip()
            if line:
                data.append(line)
            else:
                break
    except Exception as e:
        print(f"Fehler beim Lesen der seriellen Daten: {e}")
    return data

# Spannung und Strom überprüfen
def check_measurements(data):
    voltage_range = (8.0, 10)  # Spannungsbereich
    current_range = (100, 150)  # Strombereich

    report = []
    voltages = []
    currents = []

    for line in data:
        try:
            voltage, current = map(float, line.split())
            voltages.append(voltage)
            currents.append(current)
            if not (voltage_range[0] <= voltage <= voltage_range[1]):
                report.append(f"Spannung außerhalb des Bereichs: {voltage}")
            if not (current_range[0] <= current <= current_range[1]):
                report.append(f"Strom außerhalb des Bereichs: {current}")
        except ValueError:
            report.append(f"Ungültige Datenzeile: {line}")

    return report, voltages, currents


# Erstellung Report
def create_report_pdf(dut_id, report_data, voltages, currents, capacity_min, capacity_actual,
                      voltage_threshold, voltage_actual, current_threshold, current_actual,
                      max_voltage_threshold, max_voltage_actual, min_voltage_threshold, min_voltage_actual,
                      additional_notes=None):
    # Verzeichnis für Protokolle erstellen, falls nicht vorhanden
    REPORTS_DIR = "Protokolle"
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    # Aktuellen Zeitstempel hinzufügen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Erstellen des PDFs im Protokolle-Verzeichnis mit aktuellem Zeitstempel im Dateinamen
    report_path = os.path.join(REPORTS_DIR, f"{dut_id}_Pruefprotokoll_{timestamp}.pdf")
    c = canvas.Canvas(report_path, pagesize=A4)

    # Titel und DUT ID hinzufügen
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, f"Prüfprotokoll für DUT-ID: {dut_id}")

    # Entladekurve speichern
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        fig, ax = plt.subplots()
        ax.plot(voltages, label='Spannung (V)')
        ax.plot(currents, label='Strom (A)')
        ax.set_xlabel('Sekunden')
        ax.set_ylabel('Wert')
        ax.set_title(f'Entladekurve für {dut_id}')
        ax.legend()
        ax.grid(True)
        fig.savefig(temp_file.name)

        # Entladekurve zum PDF hinzufügen
        c.drawImage(temp_file.name, 100, 250, width=400, height=300)

    # Testergebnisse hinzufügen
    y_position = 700
    c.setFont("Helvetica", 12)
    c.drawString(100, y_position, "Testergebnisse:")
    y_position -= 20

    # Zusätzliche Hinweise hinzufügen, falls vorhanden
    if additional_notes:
        c.drawString(100, y_position, "Zusätzliche Hinweise:")
        y_position -= 20
        for note in additional_notes:
            c.drawString(120, y_position, note)
            y_position -= 20

    # Testergebnisse hinzufügen
    test_results = [
        (f"Mindestkapazität: {capacity_min} mAh, Ist-Kapazität: {capacity_actual} mAh", "Bestanden" if capacity_actual >= capacity_min else "Nicht bestanden"),
        (f"Grenzwert Leerlaufspannung: {voltage_threshold} V, Ist-Wert: {voltage_actual} V", "Bestanden" if voltage_actual >= voltage_threshold else "Nicht bestanden"),
        (f"Grenzwert Leerlaufstrom: {current_threshold} A, Ist-Wert: {current_actual} A", "Bestanden" if current_actual <= current_threshold else "Nicht bestanden"),
        (f"Maximale Entladespannung: {max_voltage_threshold} V, Ist-Wert: {max_voltage_actual} V", "Bestanden" if max_voltage_actual <= max_voltage_threshold else "Nicht bestanden"),
        (f"Minimale Entladespannung: {min_voltage_threshold} V, Ist-Wert: {min_voltage_actual} V", "Bestanden" if min_voltage_actual >= min_voltage_threshold else "Nicht bestanden")
    ]

    for result, status in test_results:
        c.drawString(120, y_position, result)
        c.drawString(400, y_position, status)
        y_position -= 20

    # PDF speichern und schließen
    c.showPage()
    c.save()

    print(f"Prüfprotokoll gespeichert unter: {report_path}")

def main():
    try:
        dut_id = get_dut_id()
        ser = VirtualSerial()
        start_test_environment(dut_id, ser)
        data = read_serial_data(ser)
        if not data:
            print("Keine Daten gefunden")
            return
        report, voltages, currents = check_measurements(data)

# Zusätzliche Informationen für das Prüfprotokoll
        capacity_min = 1000  # Beispiel für Mindestkapazität in mAh
        capacity_actual = 950  # Beispiel für gemessene Kapazität in mAh
        voltage_threshold = 9  # Beispiel für Schwellenwert der Leerlaufspannung in V
        voltage_actual = 8.8  # Beispiel für gemessene Leerlaufspannung in V
        current_threshold = 15  # Beispiel für Schwellenwert des Leerlaufstroms in A
        current_actual = 10  # Beispiel für gemessenen Leerlaufstrom in A
        max_voltage_threshold = 8.5  # Beispiel für maximal zulässige Entladespannung in V
        max_voltage_actual = 6.5  # Beispiel für gemessene maximale Entladespannung in V
        min_voltage_threshold = 6  # Beispiel für minimal zulässige Entladespannung in V
        min_voltage_actual = 5.5  # Beispiel für gemessene minimale Entladespannung in V
        additional_notes = ["Unplausibler Anstieg der Spannung"]

        create_report_pdf(dut_id, report, voltages, currents, capacity_min, capacity_actual,
                          voltage_threshold, voltage_actual, current_threshold, current_actual,
                          max_voltage_threshold, max_voltage_actual, min_voltage_threshold, min_voltage_actual,
                          additional_notes)

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
