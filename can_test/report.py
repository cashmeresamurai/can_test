from datetime import datetime
from fpdf import FPDF
import os
from typing_extensions import Dict, Any


class ErrorReport:
    def __init__(self):
        self.pdf = FPDF()
        self.desktop = os.path.join(os.path.expanduser("~"), "Schreibtisch")
        print("desktop path")
        print(self.desktop)

    def generate_report(self, function_name: str, error_message: str, status: dict):
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=12)

        # Header
        self.pdf.cell(
            200, 10, txt=f"Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align="C")

        # Function Info
        self.pdf.cell(
            200, 10, txt=f"Function: {function_name}", ln=1, align="L")
        self.pdf.cell(200, 10, txt=f"Error: {error_message}", ln=1, align="L")

        # Status Info
        self.pdf.cell(200, 10, txt="Current Status:", ln=1, align="L")
        for key, value in status.items():
            self.pdf.cell(200, 10, txt=f"{key}: {value}", ln=1, align="L")

        # Save to Desktop
        filename = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.pdf.output(os.path.join(self.desktop, filename))


class ScanReport:
    def __init__(self):
        self.pdf = FPDF()
        self.desktop = os.path.join(os.path.expanduser("~"), "Schreibtisch")

    def generate_report(self, error_message: str, scan_status: dict):
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=12)

        # Header
        self.pdf.cell(
            200, 10, txt=f"CAN-Scan Fehlerbericht - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align="C")

        # Error Info
        self.pdf.cell(200, 10, txt=f"Fehler: {error_message}", ln=1, align="L")

        # Status Info
        self.pdf.cell(200, 10, txt="Scan Status:", ln=1, align="L")
        for key, value in scan_status.items():
            self.pdf.cell(200, 10, txt=f"{key}: {value}", ln=1, align="L")

        # Save to Desktop
        filename = f"can_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.pdf.output(os.path.join(self.desktop, filename))


class TestReport:
    def __init__(self, can_report: Dict[str, Any]):
        self.pdf = FPDF()
        self.can_report = can_report

    def set_header(self):
        # Header
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=16)

        self.pdf.cell(w=200, h=10, txt="Test Report", ln=1, align="C")

    def write_can_report(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(w=200, h=10, txt="CAN Test Ergebnis", ln=1, align="L")

        for key, value in self.can_report.items():

            if value == "Erfolgreich":
                for device in devices:
                    for key, value in device.items():
                        if key == "serial_number" and value == "380105787":
                            self.pdf.cell(200, 10, txt=f"Gerät: Prüfmittel", ln=1, align="L")
                        elif key == "serial_number" and value != "380105787":
                            self.pdf.cell(200, 10, txt=f"Gerät: Prüfgerät", ln=1, align="L")
                        else:
                            pass
                        self.pdf.cell(200, 10, txt=f"{key}: {value}", ln=1, align="L")
            self.pdf.cell(200, 10, txt=f"{key}: {value}", ln=1, align="L")

    def save_report(self):
        filename = f"can_scan_report_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.pdf"
        self.pdf.output(os.path.join("/home/sakura/Desktop/Test Report", filename))

    def main(self):
        self.set_header()
        print(f"{self.can_report}")
        self.write_can_report()
        self.save_report()
