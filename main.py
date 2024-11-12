from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import subprocess
import json
import sys  # sys Modul importieren
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
components = Jinja2Templates(directory="templates/components")

app.mount("/static", StaticFiles(directory="static"), name="static")


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
