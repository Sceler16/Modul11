pip install pyserial
import serial
import os
from datetime import datetime


class Pruefgeraet:
    def __init__(self, ser_port):
        self.ser = serial.Serial(ser_port, baudrate=9600, timeout=1)

    def read_data(self):
        return self.ser.readline().decode().strip()


class Pruefprotokoll:
    def __init__(self, dut_id):
        self.dut_id = dut_id
        self.test_results = {}

    def add_result(self, test_name, result):
        self.test_results[test_name] = result

    def generate_report(self):
        report = f"DUT-ID: {self.dut_id}\n"
        for test_name, result in self.test_results.items():
            report += f"{test_name}: {'Bestanden' if result else 'Nicht bestanden'}\n"
        return report


def main():
    ser_port = "/dev/ttyUSB0"  # Beispiel für den seriellen Port, an den das Prüfgerät angeschlossen ist
    dut_id = input("Bitte geben Sie die DUT-ID ein: ")

    pruefgeraet = Pruefgeraet(ser_port)
    pruefprotokoll = Pruefprotokoll(dut_id)

    # Lesen der Messdaten und Prüfung
    data = pruefgeraet.read_data()
    voltage, current = map(float, data.split())

    voltage_spec_min = 3.5  # Beispiel für minimale Spannungsspezifikation
    voltage_spec_max = 4.2  # Beispiel für maximale Spannungsspezifikation
    current_spec_max = 0.5  # Beispiel für maximale Stromspezifikation

    voltage_pass = voltage_spec_min <= voltage <= voltage_spec_max
    current_pass = abs(current) <= current_spec_max
    capacity_pass = True  # Hier sollte die Prüfung der Kapazität stattfinden

    # Automatische Erstellung des Prüfprotokolls
    pruefprotokoll.add_result("Spannungstest", voltage_pass)
    pruefprotokoll.add_result("Stromtest", current_pass)
    pruefprotokoll.add_result("Kapazitätstest", capacity_pass)

    report = pruefprotokoll.generate_report()
    print(report)

    # Speichern des Prüfprotokolls
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"Pruefprotokoll_{dut_id}_{timestamp}.txt"
    with open(file_name, "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()
