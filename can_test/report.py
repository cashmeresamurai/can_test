from datetime import datetime
from fpdf import FPDF
import os


class ErrorReport:
    def __init__(self):
        self.pdf = FPDF()
        self.desktop = os.path.join(os.path.expanduser("~"), "Desktop")

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
