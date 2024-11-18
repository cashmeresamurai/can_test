from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import subprocess
import json
import sys  # sys Modul importieren
import os
import threading
from threading import Event
from send import send_can_frames
from receive import receive_can_frames

app = FastAPI()
templates = Jinja2Templates(directory="templates")
components = Jinja2Templates(directory="templates/components")

app.mount("/static", StaticFiles(directory="static"), name="static")


# Globale Variable für das Stop-Event und den Thread
receive_stop_event = None
receive_thread = None
send_stop_event = None
send_thread = None


@app.post("/receive-bytes")
async def receive_bytes(request: Request):
    global receive_stop_event, receive_thread

    data = await request.form()
    device = data.get('receive-device')

    if receive_thread and receive_thread.is_alive():
        return {
            "success": False,
            "message": "Empfang läuft bereits"
        }

    receive_stop_event = Event()
    receive_thread = threading.Thread(
        target=receive_can_frames,
        args=(device, 100000, receive_stop_event)
    )
    receive_thread.start()

    # HTMX Response für Button-Updates
    return """
    <button class="btn btn-primary flex-1" disabled
            hx-post="/receive-bytes"
            hx-include="[name='receive-device']"
            hx-swap="none">
        Empfange...
    </button>
    """


@app.post("/stop-receive")
async def stop_receive():
    global receive_stop_event, receive_thread

    if receive_stop_event and receive_thread:
        receive_stop_event.set()
        receive_thread.join()
        receive_stop_event = None
        receive_thread = None

        # HTMX Response für Button-Reset
        return """
        <button class="btn btn-primary flex-1"
                hx-post="/receive-bytes"
                hx-include="[name='receive-device']"
                hx-swap="none">
            Start Empfangen
        </button>
        """

    return {
        "success": False,
        "message": "Kein aktiver Empfang"
    }


@app.post("/send-bytes")
async def send_bytes(request: Request):
    global send_stop_event, send_thread

    data = await request.form()
    device = data.get('send-device')

    if send_thread and send_thread.is_alive():
        return {
            "success": False,
            "message": "Senden läuft bereits"
        }

    send_stop_event = Event()
    send_thread = threading.Thread(
        target=send_can_frames,
        args=(device, 100000, send_stop_event)
    )
    send_thread.start()

    # HTMX Response für Button-Update
    return """
    <button class="btn btn-primary flex-1" disabled
            hx-post="/send-bytes"
            hx-include="[name='send-device']"
            hx-swap="none">
        Sende...
    </button>
    """


@app.post("/stop-send")
async def stop_send():
    global send_stop_event, send_thread

    if send_stop_event and send_thread:
        send_stop_event.set()
        send_thread.join()
        send_stop_event = None
        send_thread = None

        # HTMX Response für Button-Reset
        return """
        <button class="btn btn-primary flex-1"
                hx-post="/send-bytes"
                hx-include="[name='send-device']"
                hx-swap="none">
            Start Senden
        </button>
        """

    return {
        "success": False,
        "message": "Kein aktives Senden"
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/start-scan", response_class=HTMLResponse)
async def start_scan(request: Request):
    try:
        result = run_initialize_with_sudo()
        return templates.TemplateResponse(
            "components/start_scan.html",
            {
                "request": request,
                "devices": result.get("devices", {}),
                "status": result.get("status", "error"),
                "error": result.get("error")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_initialize_with_sudo():
    try:
        # Setze die Berechtigungen für den seriellen Port
        # subprocess.run(['sudo', 'chmod', '666', '/dev/ttyUSB0'], check=True)

        # Hole den Pfad zum aktuellen Python-Interpreter und Arbeitsverzeichnis
        current_dir = os.getcwd()
        python_executable = sys.executable

        # Führe das Python-Skript mit sudo und korrektem PYTHONPATH aus
        cmd = [
            'sudo',
            '-S',
            'env',
            f'PYTHONPATH={current_dir}',
            python_executable,
            '-c',
            'from scanner import initialize; import json; print(json.dumps(initialize()))'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input="root\n",  # Ersetzen Sie dies mit dem tatsächlichen Passwort
            encoding='utf-8'
        )

        if result.returncode != 0:
            error_msg = f"Stdout: {result.stdout}\nStderr: {result.stderr}"
            return {"error": f"Fehler bei der Ausführung: {error_msg}"}

        # Konvertiere die Ausgabe in ein Dictionary
        try:
            # Entferne eventuelle zusätzliche Ausgaben vor dem JSON
            output_lines = result.stdout.strip().split('\n')
            json_line = output_lines[-1]  # Nimm die letzte Zeile
            return json.loads(json_line)
        except json.JSONDecodeError as e:
            return {
                "error": f"Konnte Ausgabe nicht als JSON verarbeiten: {str(e)}",
                "output": result.stdout
            }

    except Exception as e:
        return {"error": f"Ausführungsfehler: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
