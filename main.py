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


def create_report_pdf(dut_id, voltage_test_values, discharge_values, min_voltage_test, max_voltage_test, min_current_test, 
                      max_current_test, min_voltage_discharge, max_voltage_discharge, min_current_discharge, 
                      max_current_discharge):
    REPORTS_DIR = "Protokolle"
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(REPORTS_DIR, f"{dut_id}_Pruefprotokoll_{timestamp}.pdf")
    c = canvas.Canvas(report_path, pagesize=A4)

    # Titel mittig platzieren
    title = f"Prüfprotokoll für DUT-ID: {dut_id}"
    c.setFont("Helvetica-Bold", 16)
    text_width = c.stringWidth(title, "Helvetica-Bold", 16)
    page_width = A4[0]
    c.drawString((page_width - text_width) / 2, 780, title)
    # Finden Sie die Länge der voltage_test_values, um den Übergangspunkt auf der x-Achse zu bestimmen
    transition_point = len(voltage_test_values)
    
    combined_values = voltage_test_values + discharge_values

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        fig, ax = plt.subplots()
        ax.plot([i for i in range(len(combined_values))], [v for v, _ in combined_values], label='Spannung (V)')
        ax.set_xlabel('Messpunkte')
        ax.set_ylabel('Spannung (V)')
        ax.set_title(f'Entladekurve für {dut_id}')
        ax.set_ylim(min_voltage_discharge, max_voltage_discharge)
        
        # Zeichnen Sie eine vertikale Linie an der Übergangsstelle
        ax.axvline(x=transition_point, color='red', linestyle='--', linewidth=1, label='Übergang Voltage-Test/Discharge-Phase')
   
        # Zweite y-Achse für den Strom
        ax2 = ax.twinx()
        ax2.plot([i for i in range(len(combined_values))], [c for _, c in combined_values], color='tab:orange', label='Strom (A)')
        ax2.set_ylabel('Strom (A)')
        ax2.set_ylim(min_current_discharge, max_current_discharge)
        
        # Legenden hinzufügen
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper right')
       
       # X-Achse anpassen
        ax.set_xlim(0, len(combined_values))
        ax2.set_xlim(0, len(combined_values))
     
        fig.tight_layout()
        fig.savefig(temp_file.name)
        c.drawImage(temp_file.name, 50, 450, width=480, height=290)

    # Funktion zum Zeichnen von Text mit Farben
    def draw_colored_text(c, text, x, y, color):
        c.setFillColor(color)
        c.drawString(x, y, text)
        c.setFillColor("black")

    # Abstand des Ist-Werts von den Seitenrändern
    actual_value_offset = 80

    # Grenzwerte Leerlaufspannung
    voltage_test_result = "pass" if min_voltage_test <= voltage_test_values[0][0] <= max_voltage_test else "fail"
    voltage_result_color = "green" if voltage_test_result == "pass" else "red"
    voltage_test_str = f"Grenzwerte Leerlaufspannung: {min_voltage_test} - {max_voltage_test} V"
    voltage_actual_str = f"Ist-Wert: {voltage_test_values[0][0]:.2f} V"
    voltage_result_str = f"Result: {voltage_test_result}"

    c.setFont("Helvetica", 10)
    c.drawString(50, 430, voltage_test_str)
    c.drawString(page_width / 2 - c.stringWidth(voltage_actual_str) / 2 + actual_value_offset, 430, voltage_actual_str)
    draw_colored_text(c, voltage_result_str, page_width - 50 - c.stringWidth(voltage_result_str), 430, voltage_result_color)

    # Grenzwert Leerlaufstrom
    current_test_result = "pass" if min_current_test <= voltage_test_values[0][1] <= max_current_test else "fail"
    current_result_color = "green" if current_test_result == "pass" else "red"
    current_test_str = f"Grenzwert Leerlaufstrom: {min_current_test} - {max_current_test} A"
    current_actual_str = f"Ist-Wert: {voltage_test_values[0][1]:.2f} A"
    current_result_str = f"Result: {current_test_result}"

    c.drawString(50, 410, current_test_str)
    c.drawString(page_width / 2 - c.stringWidth(current_actual_str) / 2 + actual_value_offset, 410, current_actual_str)
    draw_colored_text(c, current_result_str, page_width - 50 - c.stringWidth(current_result_str), 410, current_result_color)

    # Maximale Entladespannung
    max_discharge_voltage = max(v for v, _ in discharge_values)
    max_discharge_result = "pass" if min_voltage_discharge <= max_discharge_voltage <= max_voltage_discharge else "fail"
    max_discharge_result_color = "green" if max_discharge_result == "pass" else "red"
    max_discharge_test_str = f"Maximale Entladespannung: {min_voltage_discharge} - {max_voltage_discharge} V"
    max_discharge_actual_str = f"Ist-Wert: {max_discharge_voltage:.2f} V"
    max_discharge_result_str = f"Result: {max_discharge_result}"

    c.drawString(50, 390, max_discharge_test_str)
    c.drawString(page_width / 2 - c.stringWidth(max_discharge_actual_str) / 2 + actual_value_offset, 390, max_discharge_actual_str)
    draw_colored_text(c, max_discharge_result_str, page_width - 50 - c.stringWidth(max_discharge_result_str), 390, max_discharge_result_color)

    # Minimale Entladespannung
    min_discharge_voltage = min(v for v, _ in discharge_values)
    min_discharge_result = "pass" if min_voltage_discharge <= min_discharge_voltage <= max_voltage_discharge else "fail"
    min_discharge_result_color = "green" if min_discharge_result == "pass" else "red"
    min_discharge_test_str = f"Minimale Entladespannung: {min_voltage_discharge} - {max_voltage_discharge} V"
    min_discharge_actual_str = f"Ist-Wert: {min_discharge_voltage:.2f} V"
    min_discharge_result_str = f"Result: {min_discharge_result}"

    c.drawString(50, 370, min_discharge_test_str)
    c.drawString(page_width / 2 - c.stringWidth(min_discharge_actual_str) / 2 + actual_value_offset, 370, min_discharge_actual_str)
    draw_colored_text(c, min_discharge_result_str, page_width - 50 - c.stringWidth(min_discharge_result_str), 370, min_discharge_result_color)

    # Freigegeben am und Unterschrift
    c.drawString(50, 310, f"Freigegeben am: {datetime.now().strftime('%d.%m.%Y')}")
    c.drawString(50, 260, "Unterschrift:")
    c.line(120, 260, 250, 260)

    c.save()
    print(f"Prüfprotokoll gespeichert unter: {report_path}")

def main():
    try:
        dut_id = get_dut_id()
        ser = VirtualSerial()
        voltage_test_values, discharge_values = start_test_environment(dut_id, ser)

        # Definieren Sie die Bereichsgrenzen und Kapazitätsschwelle
        min_voltage_test = 8.0
        max_voltage_test = 10.0
        min_current_test = 0.0
        max_current_test = 1.0
        min_voltage_discharge = 5.8
        max_voltage_discharge = 10.0
        min_current_discharge = 100.0
        max_current_discharge = 150.0

        # Erstellen des Prüfprotokolls
        create_report_pdf(dut_id, voltage_test_values, discharge_values, min_voltage_test, max_voltage_test, min_current_test, 
                              max_current_test, min_voltage_discharge, max_voltage_discharge, min_current_discharge, 
                              max_current_discharge)

    except Exception as e:
        print(f"Fehler: {e}")


if __name__ == "__main__":
    main()
