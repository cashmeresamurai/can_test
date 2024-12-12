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

        self.pdf.cell(w=200, h=10, text="Test Report", ln=1, align="C")

    def write_can_report(self):
        """
        Erstellt einen formatierten CAN Test Report im PDF Format
        """
        # Schriftgröße setzen
        self.pdf.set_font_size(14)

        # Test Report Header
        self.pdf.cell(w=200, h=10, text="Test Report", ln=1, align="L")

        # CAN Test Ergebnis Header
        self.pdf.cell(w=200, h=10, text="CAN Test Ergebnis", ln=1, align="L")

        # Status und Timestamp
        if "status" in self.can_report:
            self.pdf.cell(
                w=200, h=10, text=f"Status: {self.can_report['status']}", ln=1, align="L")

        if "timestamp" in self.can_report:
            self.pdf.cell(
                w=200, h=10, text=f"timestamp: {self.can_report['timestamp']}", ln=1, align="L")

        # Wenn Geräte vorhanden sind
        if "devices" in self.can_report:
            # Überschrift für Geräteliste
            self.pdf.cell(w=200, h=10, text="Getestete Geräte:",
                          ln=1, align="L")

            # Iteration über alle Geräte
            for device in self.can_report["devices"]:
                # Gerätetyp bestimmen
                if device.get("serial_number") == "380105787":
                    self.pdf.cell(
                        w=200, h=10, text="Gerät: Prüfmittel", ln=1, align="L")
                else:
                    self.pdf.cell(
                        w=200, h=10, text="Gerät: Prüfgerät", ln=1, align="L")

                # Geräteinformationen ausgeben
                for key, value in device.items():
                    self.pdf.cell(
                        w=200, h=10, text=f"{key}: {value}", ln=1, align="L")

                # Leerzeile zwischen Geräten
                self.pdf.cell(w=200, h=5, text="", ln=1, align="L")

    def generate_videosignal_report_1(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(w=200, h=10, text=f"Videosignaltest 1", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.videosignal_1.items():
            self.pdf.cell(w=200, h=10, text=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, text="", ln=1, align="L")

    def generate_videosignal_report_2(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(w=200, h=10, text=f"Videosignaltest 2", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.videosignal_2.items():
            self.pdf.cell(w=200, h=10, text=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, text="", ln=1, align="L")

    def generate_vga_report(self):
        self.pdf.set_font_size(14)

        self.pdf.cell(
            w=200, h=10, text="Q-Leica Display-Port Test", ln=1, align="L")

        self.pdf.set_font_size(12)

        for key, value in self.vga_status.items():
            self.pdf.cell(w=200, h=10, text=f"{key}: {value}", ln=1, align="L")

        self.pdf.cell(w=200, h=5, text="", ln=1, align="L")

    def save_report(self):
        filename = f"can_scan_report_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.pdf"
        self.pdf.output(os.path.join(
            "/home/stryker/Schreibtisch/Test Report", filename))

    def main(self):
        self.set_header()
        print(f"{self.can_report}")
        self.write_can_report()
        if self.videosignal_1 != None:
            self.generate_videosignal_report_1()

        if self.videosignal_2 != None:
            self.generate_videosignal_report_2()

        if self.vga_status != None:
            self.generate_vga_report()
        self.save_report()
