import os
import sys
import io
import subprocess
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

def check_measurements(data):
    voltage_range = (7.0, 10)  # Beispiel für Spannungsbereich
    current_range = (0, 20)  # Beispiel für Strombereich

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

def create_report(dut_id, report_data, voltages, currents):
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    REPORTS_DIR = os.path.join(SCRIPT_DIR, "Protokolle")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    report_path = os.path.join(REPORTS_DIR, f"{dut_id}_Pruefprotokoll.pdf")
    c = canvas.Canvas(report_path)

    c.drawString(100, 800, f"Prüfprotokoll für DUT-ID: {dut_id}")
    c.drawString(100, 780, "Prüfungsergebnisse:")
    y_position = 760
    for item in report_data:
        c.drawString(100, y_position, item)
        y_position -= 20

    c.showPage()
    c.save()

    # Plot the discharge curve
    plt.figure()
    plt.plot(voltages, label='Voltage (V)')
    plt.plot(currents, label='Current (A)')
    plt.xlabel('Measurement Points')
    plt.ylabel('Values')
    plt.title(f'Discharge Curve for {dut_id}')
    plt.legend()
    plt.grid(True)

    # Save plot as an image
    plot_path = os.path.join(REPORTS_DIR, f"{dut_id}_DischargeCurve.png")
    plt.savefig(plot_path)

    print(f"Prüfprotokoll gespeichert unter: {report_path}")
    print(f"Entladekurve gespeichert unter: {plot_path}")

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
        create_report(dut_id, report, voltages, currents)
        
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
