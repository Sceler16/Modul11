import os
import subprocess

# Funktion zum Eingeben der DUT-ID
def get_dut_id():
    return input("Geben Sie die DUT-ID ein (z.B. BatXDev20240510): ")

# Funktion zum Starten der Testumgebung mit der gegebenen DUT-ID
def start_test_environment(dut_id):
    # Rufen Sie `testdata.py` mit der DUT-ID als Kommandozeilenargument auf
    subprocess.run(["python3", "testdata.py", dut_id], check=True)

# Hauptfunktion
def main():
    dut_id = get_dut_id()  # Eingabe der DUT-ID
    start_test_environment(dut_id)  # Starten der Testumgebung mit der DUT-ID

if __name__ == "__main__":
    main()