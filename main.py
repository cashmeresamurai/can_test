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
from send import send_can_frames, send_image_over_can
from receive import receive_can_frames, receive_image_over_can
from pprint import pprint
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
        target=receive_image_over_can,
        args=(device, 100000, receive_stop_event)
    )
    receive_thread.start()

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
        target=send_image_over_can,
        args=(device, 100000, send_stop_event)
    )
    send_thread.start()

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


@app.get("/step-1", response_class=HTMLResponse)
def step_1(request: Request):
    return templates.TemplateResponse("step_1.html", {"request": request})


@app.get("/step-2", response_class=HTMLResponse)
def step_2(request: Request):
    return templates.TemplateResponse("step_2.html", {"request": request})


@app.get("/step-3", response_class=HTMLResponse)
def step_3(request: Request):
    return templates.TemplateResponse("step_3.html", {"request": request})


def get_devices_list(initialize_result):
    try:
        # Convert string to dictionary if needed
        if isinstance(initialize_result, str):
            initialize_result = json.loads(initialize_result)

        if isinstance(initialize_result, dict):
            if 'devices' in initialize_result:
                devices = []
                for port, info in initialize_result['devices'].items():
                    device_info = info.copy()
                    device_info['port'] = port
                    devices.append(device_info)
                print(len(devices))
                return devices, "success", None
            elif 'status' in initialize_result and initialize_result['status'] == 'success':
                return [], "success", None
            elif 'error' in initialize_result:
                return [], "error", initialize_result['error']

        return [], "error", "Invalid data format"

    except Exception as e:
        return [], "error", str(e)


@app.get("/start-scan", response_class=HTMLResponse)
async def start_scan(request: Request):
    try:
        initialize_result = run_initialize_with_sudo()
        devices, status, error = get_devices_list(initialize_result)

        if error:
            raise HTTPException(status_code=500, detail=error)

        return templates.TemplateResponse(
            "components/start_scan.html",
            {
                "request": request,
                "devices": devices,
                "status": status,
                "error": None
            }
        )
    except Exception as e:
        pprint(e)
        raise HTTPException(status_code=500, detail=str(e))


def run_initialize_with_sudo():
    try:
        current_dir = os.getcwd()
        python_executable = sys.executable

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
            input="root\n",
            encoding='utf-8'
        )

        if result.returncode != 0:
            return {"error": f"Execution error: {result.stderr}"}

        # Clean and parse output
        output_lines = result.stdout.strip().split('\n')
        json_line = output_lines[-1]  # Take the last line
        return json.loads(json_line)

    except Exception as e:
        return {"error": f"Execution error: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
