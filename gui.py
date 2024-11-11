import customtkinter
import threading
import sys
import io
from scanner import initialize

class MainWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguriere das Erscheinungsbild
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        # Fenster-Einstellungen
        self.title("CAN Test Interface")
        self.geometry("800x600")

        # Layout erstellen
        self.setup_layout()

    def setup_layout(self):
        # Header
        self.header = customtkinter.CTkLabel(
            self,
            text="CAN Test Interface",
            font=("Helvetica", 24, "bold")
        )
        self.header.pack(pady=20)

        # Status Label
        self.status = customtkinter.CTkLabel(
            self,
            text="Ready",
            font=("Helvetica", 12)
        )
        self.status.pack(pady=10)

        # Start Button
        self.start_button = customtkinter.CTkButton(
            self,
            text="Start Scanner",
            command=self.start_test,
            width=200,
            height=40
        )
        self.start_button.pack(pady=10)

        # Text Output
        self.text_area = customtkinter.CTkTextbox(
            self,
            width=700,
            height=400
        )
        self.text_area.pack(pady=20, padx=20, expand=True, fill="both")

    def append_text(self, text):
        self.text_area.configure(state="normal")
        self.text_area.insert("end", str(text) + "\n")
        self.text_area.see("end")
        self.text_area.configure(state="disabled")

    def update_status(self, text):
        self.status.configure(text=text)

    def update_button_state(self, state):
        self.start_button.configure(state="normal" if state else "disabled")

    def start_test(self):
        self.update_button_state(False)
        self.update_status("Starting device initialization...")
        self.append_text("Starting initialization...")

        # Starte den Test in einem separaten Thread
        thread = threading.Thread(target=self.run_scanner)
        thread.daemon = True
        thread.start()

    def run_scanner(self):
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # Redirect output
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Set default argv
            old_argv = sys.argv
            sys.argv = ['scanner.py']

            # Run scanner
            main()

            # Restore argv
            sys.argv = old_argv

            # Get captured output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            # Display output in GUI
            if stdout_output:
                for line in stdout_output.splitlines():
                    if line.strip():
                        self.after(0, self.append_text, line)

            # Display any errors
            if stderr_output:
                for line in stderr_output.splitlines():
                    if line.strip():
                        self.after(0, self.append_text, f"Error: {line}")

            self.after(0, self.scan_complete)

        except Exception as e:
            self.after(0, self.append_text, f"Exception occurred: {str(e)}")
            self.after(0, self.scan_failed)

        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            stdout_capture.close()
            stderr_capture.close()

    def scan_complete(self):
        self.update_button_state(True)
        self.update_status("Scan complete")
        self.append_text("Initialization completed successfully")

    def scan_failed(self):
        self.update_button_state(True)
        self.update_status("Scan failed")

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
