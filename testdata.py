import os
import sys
import time

class VirtualSerial:
    def __init__(self):
        self.buffer = []

    def write(self, data):
        self.buffer.append(data)

    def readline(self):
        if self.buffer:
            return self.buffer.pop(0)
        return ""

# Überprüfe, ob eine Testdatei passend zur eingegebenen DUT-ID im Verzeichnis BatDat vorhanden ist
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
        test_data = [line.strip() for line in lines]  # Nur die Werte ohne Bezeichnungen lesen
        return test_data

# Lese 1. Zeile für Voltage-Test
def voltage_test(dut_id, serial_port):
    print("Voltage Test")
    pretest_data = read_test_data(dut_id)[0]  # Erste Zeile
    print(pretest_data)
    serial_port.write(pretest_data + "\n")
    time.sleep(0.1)

# Lese 2. und folgende Zeilen für Discharge Test
def discharge_phase(dut_id, serial_port):
    print("Discharge Phase")
    discharge_data = read_test_data(dut_id)[1:]  # Zweite Zeile und folgende
    for data in discharge_data:
        print(data)
        serial_port.write(data + "\n")
        time.sleep(0.1)  # Simuliere 1 Sekunde Pause zwischen den Messungen
    

def main():
    if len(sys.argv) < 2:
        print("Fehler: DUT-ID muss als Kommandozeilenargument übergeben werden.")
        sys.exit(1)
    dut_id = sys.argv[1]

    try:
        ser = VirtualSerial()
        print(f"DUT-ID empfangen, Prüfung startet")
        result = check_directory(dut_id)
        ser.write(result + "\n")

        if "does not exist" in result:
            ser.write("false\n")
        else:
            ser.write("true\n")

            # Starte Voltage Test
            voltage_test(dut_id, ser)

            # Starte Discharge Phase
            discharge_phase(dut_id, ser)

        print("Ende des Tests\n")
        ser.write("Ende des Tests\n")

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
