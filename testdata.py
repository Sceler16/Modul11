import sys
import os
import serial
import time

# Überprüfen, ob die DUT-ID als Kommandozeilenargument übergeben wurde
if len(sys.argv) < 2:
    print("Fehler: DUT-ID muss als Kommandozeilenargument übergeben werden. Starten Sie dazu main.py")
    sys.exit(1)

dut_id = sys.argv[1]  # DUT-ID aus Kommandozeilenargument
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BATDAT_DIR = os.path.join(SCRIPT_DIR, "BatDat")

# Funktion zum Einlesen der Testdaten aus einer Datei
def read_test_data(dut_id):
    file_path = os.path.join(BATDAT_DIR, f"{dut_id}.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Testdatei für DUT-ID '{dut_id}' nicht gefunden.")
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# Funktion zum Simulieren der Testumgebung
def simulate_test_environment(serial_port, test_data):
    with serial.Serial(serial_port, 9600, timeout=1) as ser:
        # Simulieren der Voltage-Test-Phase
        ser.write(f"{test_data[0]}\n".encode())  # Voltage-Test-Werte
        response = ser.readline().decode().strip()  # Warten auf Reaktion

        if response.lower() == "true":
            # Simulieren der Discharge-Phase
            time.sleep(1)  # Kurze Verzögerung vor dem Start
            for line in test_data[1:]:
                ser.write(f"{line}\n".encode())
                time.sleep(8)  # Verzögerung zwischen den Daten
        else:
            print("Voltage-Test nicht erfolgreich, Abbruch.")

        print("Testumgebung abgeschlossen.")

# Serieller Port (Anpassen nach Bedarf)
vir_serial_port = "/dev/ttyv1"  # Virtueller Port

try:
    test_data = read_test_data(dut_id)  # Einlesen der Testdaten
    simulate_test_environment(serial_port, test_data)  # Simulieren der Testumgebung
except FileNotFoundError as e:
    print(str(e))
