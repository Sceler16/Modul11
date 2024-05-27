import os
import sys
import io
import subprocess
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt


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


def get_dut_id():
    dut_id = input("Geben Sie die DUT-ID ein (z.B. BatXDev20240510): ")
    if not dut_id:
        raise ValueError("DUT-ID darf nicht leer sein.")
    return dut_id

def start_test_environment(dut_id, serial_port):
    voltage_test_values = []
    discharge_values = []

    try:
        # Sende DUT-ID an testdata.py und starte es als Subprozess
        result = subprocess.run([sys.executable, "testdata.py", dut_id], capture_output=True, text=True)
        response = result.stdout.strip().split('\n')  # Antwort von testdata.py erhalten
        #print(F"Antwort: {response}")

        voltage_test_started = False
        discharge_phase_started = False

        for line in response:
            print(f"Empfangen: {line}")
            if "Voltage Test" in line:
                voltage_test_started = True
            elif "Discharge Phase" in line:
                discharge_phase_started = True
                voltage_test_started = False
            elif "Ende des Tests" in line:
                discharge_phase_started = False

             # Wenn der Spannungstest läuft, füge die Werte zu den entsprechenden Listen hinzu
            if voltage_test_started and any(char.isdigit() for char in line):
                voltage, current = map(float, line.split())
                voltage_test_values.append((voltage, current))

           # Wenn die Entladephase läuft, füge die Werte zu den entsprechenden Listen hinzu
            if discharge_phase_started and any(char.isdigit() for char in line):
                voltage, current = map(float, line.split())
                discharge_values.append((voltage, current))

        return voltage_test_values, discharge_values

    except Exception as e:
        print(f"Fehler bei der virtuellen seriellen Kommunikation: {e}")
        raise


def check_measurements(voltage_test_values, discharge_values, voltage_range, current_range, capacity_limit):
    unplausible_data = False

    # Überprüfung der Spannungswerte
    for voltage, _ in voltage_test_values:
        if voltage < voltage_range[0] or voltage > voltage_range[1]:
            print("Fehler: Spannung außerhalb des spezifizierten Bereichs!")
            unplausible_data = True

    # Überprüfung der Stromwerte
    for _, current in voltage_test_values + discharge_values:
        if current < current_range[0] or current > current_range[1]:
            print("Fehler: Strom außerhalb des spezifizierten Bereichs!")
            unplausible_data = True

    # Überprüfung der Kapazität
    total_capacity = sum(voltage * current for voltage, current in discharge_values)
    if total_capacity < capacity_limit:
        print("Fehler: Kapazität nicht erreicht!")
        unplausible_data = True

    return unplausible_data


def create_report_pdf(dut_id, voltages, currents, voltage_range, current_range, unplausible_data):
    REPORTS_DIR = "Protokolle"
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(REPORTS_DIR, f"{dut_id}_Pruefprotokoll_{timestamp}.pdf")
    c = canvas.Canvas(report_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, f"Prüfprotokoll für DUT-ID: {dut_id}")

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
        c.drawImage(temp_file.name, 100, 250, width=400, height=300)

    y_position = 700
    c.setFont("Helvetica", 12)
    c.drawString(100, y_position, "Testergebnisse:")
    y_position -= 20

    test_results = [
        (f"Grenzwerte Spannung: {voltage_range} V", "Überprüft"),
        (f"Grenzwerte Strom: {current_range} mA", "Überprüft"),
        ("Unplausible Daten vorhanden" if unplausible_data else "Keine unplausiblen Daten gefunden", "Überprüft")
    ]

    for result, status in test_results:
        c.drawString(120, y_position, result)
        c.drawString(400, y_position, status)
        y_position -= 20

    c.drawString(100, y_position - 20, "Freigabe:")
    c.line(150, y_position - 20, 300, y_position - 20)

    c.showPage()
    c.save()
    print(f"Prüfprotokoll gespeichert unter: {report_path}")


def main():
    try:
        dut_id = get_dut_id()
        ser = VirtualSerial()
        voltage_test_values, discharge_values = start_test_environment(dut_id, ser)

        # Definieren Sie die Bereichsgrenzen und Kapazitätsschwelle
        voltage_range = (6.0, 9.0)
        current_range = (100, 150.0)
        capacity_limit = 2000

        # Überprüfen der Messwerte
        unplausible_data = check_measurements(voltage_test_values, discharge_values, voltage_range, current_range, capacity_limit)

        # Erstellen des Prüfprotokolls
        create_report_pdf(dut_id, [voltage for voltage, _ in discharge_values], 
                          [current for _, current in discharge_values], voltage_range, current_range, unplausible_data)

    except Exception as e:
        print(f"Fehler: {e}")


if __name__ == "__main__":
    main()
