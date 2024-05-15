import io
import os
import sys
import time


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

# Überpfrüfe ob eine Testdatei passsend zur Eingegebenen DUT-ID im Verzeichnis BatDat vorhanden ist
def check_directory(dut_id):
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    BATDAT_DIR = os.path.join(SCRIPT_DIR, "BatDat")
    file_path = os.path.join(BATDAT_DIR, f"{dut_id}.txt")
    if os.path.exists(file_path):
        return f"File {file_path} exists."
    else:
        return f"File {file_path} does not exist."

# Auslesen der Testdaten aus der txt Datei
def read_test_data(dut_id):
    file_path = f"BatDat/{dut_id}.txt"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Testdatei für DUT-ID '{dut_id}' nicht gefunden.")
    with open(file_path, 'r') as f:
        lines = f.readlines()
        test_data = [tuple(map(float, line.split())) for line in lines]
        return test_data
    
# Lese 1. Zeile für Voltage-Test
def voltage_test(dut_id, serial_port):
    print("Starte Voltage Test")
    pretest_data = read_test_data(dut_id)[0]  # Erste Zeile
    voltage, current = pretest_data
    serial_port.write(f"{voltage} {current}\n")
    print(f"Spannung: {voltage}, Strom: {current}")

# Lese 2. und folgende Zeilen für Discharge Test
def discharge_phase(dut_id, serial_port):
    print("Starte Discharge Phase")
    discharge_data = read_test_data(dut_id)[1:] # Zweite Zeile und folgende
    for voltage, current in discharge_data:
        serial_port.write(f"{voltage} {current}\n")
        print(f"Spannung: {voltage}, Strom: {current}")
        time.sleep(0.1)  # Simuliere 8 Sekunden Pause zwischen den Messungen

def main():
    if len(sys.argv) < 2:
        print("Fehler: DUT-ID muss als Kommandozeilenargument übergeben werden.")
        sys.exit(1)
    
    dut_id = sys.argv[1]

    try:
        ser = VirtualSerial()
        print(f"DUT-ID empfangen")
        result = check_directory(dut_id)
        ser.write(result + "\n")
        ser.write("true\n")

        # Starte Voltage Test
        voltage_test(dut_id, ser)

        # Starte Discharge Phase
        discharge_phase(dut_id, ser)

        # End-Of-Test Phase (Ende der Datenübertragung)
        print("Ende des Tests")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
