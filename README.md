# Modul11


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

def check_measurements(voltage_test_values, discharge_values, min_voltage_test, max_voltage_test, min_current_test, max_current_test, 
                       min_voltage_discharge, max_voltage_discharge, min_current_discharge, max_current_discharge):
    unplausible_data = False

    # Überprüfung der Leerlaufspannung
    for voltage, _ in voltage_test_values:
        if not (min_voltage_test <= voltage <= max_voltage_test):
            unplausible_data = True
            break

    # Überprüfung des Leerlaufstroms
    for _, current in discharge_values:
        if not (min_current_test <= current <= max_current_test):
            unplausible_data = True
            break

    # Max. Entladungsspannung
    max_discharge_voltage = max(voltage for voltage, _ in discharge_values)
    if not (min_voltage_discharge <= max_discharge_voltage <= max_voltage_discharge):
        unplausible_data = True

    # Min. Entladungsstrom
    min_discharge_current = min(current for _, current in discharge_values)
    if not (min_current_discharge <= min_discharge_current <= max_current_discharge):
        unplausible_data = True

    return unplausible_data

        # Überprüfen der Messwerte
        unplausible_data = check_measurements(voltage_test_values, discharge_values, min_voltage_test, max_voltage_test, min_current_test, 
                                              max_current_test, min_voltage_discharge, max_voltage_discharge, min_current_discharge, 
                                              max_current_discharge)