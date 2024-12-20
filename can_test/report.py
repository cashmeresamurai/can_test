from datetime import datetime
from fpdf import FPDF
import os
from typing_extensions import Dict, Any


class TestReport:
    def __init__(self,
                 can_report,
                 videosignal_1,
                 videosignal_2,
                 vga_status
                 ):
        self.pdf = FPDF()
        self.can_report = can_report
        self.videosignal_1 = videosignal_1
        self.videosignal_2 = videosignal_2
        self.vga_status = vga_status

    def set_header(self):
        # Header
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=16)

        self.pdf.cell(w=200, h=10, txt="Test Report", ln=1, align="C")

    def write_can_report(self):
        """
        Erstellt einen formatierten CAN Test Report im PDF Format
        """
        # Schriftgröße setzen
        self.pdf.set_font_size(14)

        # CAN Test Ergebnis Header
        self.pdf.cell(w=200, h=10, txt="CAN Test Ergebnis", ln=1, align="L")

        self.pdf.set_font_size(12)

        # Status und Timestamp
        if "Status" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Status: {self.can_report['Status']}", ln=1, align="L")

        if "timestamp" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Zeitpunkt: {self.can_report['timestamp']}", ln=1, align="L")
        elif "Datum" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Zeitpunkt: {self.can_report['Datum']}", ln=1, align="L")

        # Alle möglichen Fehlermeldungen
        if "Fehler" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Fehlermeldung: {self.can_report['Fehler']}", ln=1, align="L")

        if "Fehlermeldung" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Fehlermeldung: {self.can_report['Fehlermeldung']}", ln=1, align="L")

        if "error_details" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Fehlerdetails: {self.can_report['error_details']}", ln=1, align="L")

        if "error_type" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Fehlertyp: {self.can_report['error_type']}", ln=1, align="L")

        if "device_filtering" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Gerätefilterung: {self.can_report['device_filtering']}", ln=1, align="L")

        if "initialization" in self.can_report:
            self.pdf.cell(
                w=200, h=10, txt=f"Initialisierung: {self.can_report['initialization']}", ln=1, align="L")

        # Wenn Geräte vorhanden sind
        if "devices" in self.can_report:
            self.pdf.cell(w=200, h=10, txt="Getestete Geräte:",
                          ln=1, align="L")

            for device in self.can_report["devices"]:
                if device.get("serial_number") == "380105787":
                    self.pdf.cell(
                        w=200, h=10, txt="Gerät: Prüfmittel", ln=1, align="L")
                else:
                    self.pdf.cell(
                        w=200, h=10, txt="Gerät: Prüfgerät", ln=1, align="L")

                for key, value in device.items():
                    self.pdf.cell(
                        w=200, h=10, txt=f"{key}: {value}", ln=1, align="L")

                # Leerzeile zwischen Geräten
                self.pdf.cell(w=200, h=5, txt="", ln=1, align="L")

        # Abschließende Leerzeile
        self.pdf.cell(w=200, h=5, txt="", ln=1, align="L")

    def generate_videosignal_report_1(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(w=200, h=10, txt=f"Videosignaltest 1", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.videosignal_1.items():
            self.pdf.cell(w=200, h=10, txt=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, txt="", ln=1, align="L")

    def generate_videosignal_report_2(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(w=200, h=10, txt=f"Videosignaltest 2", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.videosignal_2.items():
            self.pdf.cell(w=200, h=10, txt=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, txt="", ln=1, align="L")

    def generate_vga_report(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(
            w=200, h=10, txt="Q-Leica Display-Port Test", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.vga_status.items():
            self.pdf.cell(w=200, h=10, txt=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, txt="", ln=1, align="L")

    def save_report(self):
        filename = f"can_scan_report_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.pdf"
        self.pdf.output(os.path.join(
            "/home/stryker/Schreibtisch/Test Report", filename))

    def main(self):
        self.set_header()
        if self.can_report is not None:
            self.write_can_report()
            # Leerzeile nach dem CAN Report
            self.pdf.cell(w=200, h=10, txt="", ln=1, align="L")

        if self.videosignal_1 is not None:
            self.generate_videosignal_report_1()

        if self.videosignal_2 is not None:
            self.generate_videosignal_report_2()

        if self.vga_status is not None:
            self.generate_vga_report()

        self.save_report()
