import asyncio
from datetime import datetime
from typing import Any, TypedDict
from pymonctl import ScreenValue
from typing_extensions import Dict, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from result import Err, Ok, Result
import uvicorn
import subprocess
import json
import sys  # sys Modul importieren
import os
import threading
from threading import Event

from can_test.report import ErrorReport, ScanReport
from can_test.screen import check_vga_adapter
from .scanner import FoundDevice, FoundDeviceError, initialize
from .send import send_can_frames, send_image_over_can
from .receive import receive_can_frames, receive_image_over_can
from pprint import pprint

import os
from pathlib import Path
app = FastAPI()

# Get the base directory (where pyproject.toml is)
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)

# Update templates and static paths
templates = Jinja2Templates(directory=str(BASE_DIR / "can_test/templates"))
components = Jinja2Templates(directory=str(
    BASE_DIR / "can_test/templates/components"))

# Update static path to match the new structure
static_dir = BASE_DIR / "can_test/static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class TestDevice(TypedDict):
    name: str
    port: str


# Globale Variable für das Stop-Event und den Thread
receive_stop_event = None
receive_thread = None
send_stop_event = None
send_thread = None
pruefhilfsmittel: TestDevice = None
pruefgeraet: TestDevice = None


async def receive_bytes(test_device: TestDevice) -> Result[bool, str]:
    try:
        global receive_stop_event, receive_thread
        receive_stop_event = Event()
        receive_thread = threading.Thread(
            target=receive_image_over_can,
            args=(test_device["port"], 100000, receive_stop_event)
        )
        receive_thread.start()
        return Ok(True)
    except Exception as e:
        error_report = ErrorReport()
        status = {
            "device_name": test_device["name"],
            "device_port": test_device["port"],
            "receive_thread_active": receive_thread is not None if receive_thread else False,
            "stop_event_set": receive_stop_event.is_set() if receive_stop_event else False
        }
        error_report.generate_report("receive_bytes", str(e), status)
        receive_stop_event = None
        receive_thread = None
        return Err(f"Der Startvorgang für {test_device['name']} konnte nicht gestartet werden.")


async def stop_receive() -> Result[bool, str]:
    try:
        global receive_stop_event, receive_thread

        if receive_stop_event and receive_thread:
            receive_stop_event.set()
            receive_thread.join()
            receive_stop_event = None
            receive_thread = None
            return Ok(True)
        else:
            return Err("Der Endvorgang konnte nicht gestoppt werden.")
    except:
        receive_stop_event = None
        receive_thread = None
        return Err(f"Der Endvorgang konnte nicht gestoppt werden.")


async def send_bytes(test_device: TestDevice) -> Result[bool, str]:
    try:
        global send_stop_event, send_thread
        send_stop_event = Event()
        send_thread = threading.Thread(
            target=send_image_over_can,
            args=(test_device["port"], 100000, send_stop_event)
        )
        send_thread.start()
        return Ok(True)
    except Exception as e:
        error_report = ErrorReport()
        status = {
            "device_name": test_device["name"],
            "device_port": test_device["port"],
            "send_thread_active": send_thread is not None if send_thread else False,
            "stop_event_set": send_stop_event.is_set() if send_stop_event else False
        }
        error_report.generate_report("send_bytes", str(e), status)
        send_stop_event = None
        send_thread = None
        return Err(f"Der Startvorgang für das Senden des Testbilds für '{test_device['name']}' konnte nicht gestartet werden")


async def stop_send():
    global send_stop_event, send_thread

    if send_stop_event and send_thread:
        send_stop_event.set()
        send_thread.join()
        send_stop_event = None
        send_thread = None


@app.get("/can-send-receive-1", response_class=HTMLResponse)
async def send_receive_1(request: Request):
    global pruefgeraet, pruefhilfsmittel

    # Starte Empfang auf Prüfgerät
    receive_result = await receive_bytes(pruefgeraet)
    if isinstance(receive_result, Err):
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": receive_result.unwrap_err()
            }
        )

    # Starte Senden auf Prüfhilfsmittel
    send_result = await send_bytes(pruefhilfsmittel)
    await asyncio.sleep(4)
    if isinstance(send_result, Err):
        # Stoppe den Empfang falls das Senden fehlschlägt
        await stop_receive()
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": send_result.unwrap_err()
            }
        )

    # Wenn beide Operationen erfolgreich waren
    if send_result.is_ok() and receive_result.is_ok():
        # Stoppe beide Operationen
        await stop_receive()
        await stop_send()

        return templates.TemplateResponse(
            "components/success_1.html",
            {
                "request": request,
                "message": "Test 1: Kommunikation erfolgreich durchgeführt"
            }
        )


@app.get("/can-send-receive-2", response_class=HTMLResponse)
async def send_receive_2(request: Request):
    global pruefgeraet, pruefhilfsmittel

    # Starte Empfang auf Prüfgerät
    receive_result = await receive_bytes(pruefhilfsmittel)
    if isinstance(receive_result, Err):
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": receive_result.unwrap_err()
            }
        )

    # Starte Senden auf Prüfhilfsmittel
    send_result = await send_bytes(pruefgeraet)
    await asyncio.sleep(4)
    if isinstance(send_result, Err):
        # Stoppe den Empfang falls das Senden fehlschlägt
        await stop_receive()
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": send_result.unwrap_err()
            }
        )

    # Wenn beide Operationen erfolgreich waren
    if send_result.is_ok() and receive_result.is_ok():
        # Stoppe beide Operationen
        await stop_receive()
        await stop_send()

        return templates.TemplateResponse(
            "components/success_2.html",
            {
                "request": request,
                "message": "Test 2: Kommunikation erfolgreich durchgeführt"
            }
        )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/step-1", response_class=HTMLResponse)
def step_1(request: Request):
    return templates.TemplateResponse("step_1.html", {"request": request})


@app.get("/step-2", response_class=HTMLResponse)
def step_2(request: Request):
    return templates.TemplateResponse("step_2.html", {"request": request})


@app.get("/create-report", response_class=HTMLResponse)
def create_report(request: Request):
    return templates.TemplateResponse("create_report.html", {"request": request})


@app.get("/step-3", response_class=HTMLResponse)
def step_3(request: Request):
    return templates.TemplateResponse("step_3.html", {"request": request})


@app.get("/start-scan", response_class=HTMLResponse)
async def start_scan(request: Request):
    initialize_result: Result[Dict[str, Any], str] = initialize()

    if isinstance(initialize_result, Err):
        error_message: str = initialize_result.unwrap_err()
        report = ScanReport()
        scan_status = {
            "initialization": "failed",
            "error_type": "initialization_error",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        report.generate_report(error_message, scan_status)
        data: Dict[str, Any] = {
            "request": request,
            "error_message": error_message
        }
        return templates.TemplateResponse(
            name="components/error.html",
            context=data,
        )

    elif isinstance(initialize_result, Ok):
        try:
            untyped_devices: Dict[str, Any] = initialize_result.ok()
            devices_result: List[Dict[str, str]] = untyped_devices["devices"]
            ports: List[str] = untyped_devices.get(
                "ports", ['/dev/ttyUSB0', '/dev/ttyUSB1'])
            typed_device_list: List[Device] = []

            for i, device in enumerate(devices_result):
                device_result = device.unwrap()
                typed_device: Device = {
                    "serial_number": device_result["serial_number"],
                    "hardware": device_result["hardware"],
                    "firmware": device_result["firmware"],
                    "status": device_result["status"],
                    "port": ports[i] if i < len(ports) else f"/dev/ttyUSB{i}"
                }
                typed_device_list.append(typed_device)

            devices: Result[List[Device], str] = filter_devices(
                devices=typed_device_list)

            if devices.is_err():
                error_message1: str = devices.unwrap_err()
                report = ScanReport()
                scan_status = {
                    "initialization": "success",
                    "device_filtering": "failed",
                    "found_devices": len(typed_device_list),
                    "error_type": "device_filter_error",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                report.generate_report(error_message1, scan_status)
                err_data: Dict[str, Any] = {
                    "request": request,
                    "error_message": error_message1
                }
                return components.TemplateResponse(name="error.html",
                                                   context=err_data)
            elif devices.is_ok():
                return templates.TemplateResponse(
                    "components/start_scan.html",
                    {
                        "request": request,
                        "devices": devices.ok(),
                        "status": "success",
                        "error": None
                    }
                )

        except Exception as e:
            report = ScanReport()
            scan_status = {
                "initialization": "success",
                "error_type": "processing_error",
                "error_details": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            report.generate_report(str(e), scan_status)
            return templates.TemplateResponse(
                name="components/error.html",
                context={"request": request, "error_message": str(e)}
            )


class Device(TypedDict):
    serial_number: str
    firmware: str
    hardware: str
    status: str
    port: str


def filter_devices(devices: List[Device]) -> Result[List[Device], str]:
    global pruefhilfsmittel, pruefgeraet
    print(devices)
    filtered_devices: List[Device] = []
    match len(devices):
        case 0:
            return Err("Es wurden keine USB-CAN Geräte gefunden. Bitte stellen Sie sicher, dass Sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")

        case 1:
            return Err("Es wurde nur ein USB-CAN Gerät gefunden. Bitte stellen Sie sicher, dass Sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")

        case 2:
            for found_device in devices:
                if found_device["serial_number"] == "380105787":
                    # Use global variable without annotation
                    pruefhilfsmittel = {
                        "name": "Prüfhilfsmittel",
                        "port": found_device["port"]

                    }
                    print("pruefhilfsmittel")
                    pprint(f"{pruefhilfsmittel}")
                else:
                    pruefgeraet = {
                        "name": "Prüfgerät",
                        "port": found_device["port"]
                    }
                    print("pruefgeraet")
                    pprint(f"{pruefgeraet}")
                device: Device = {
                    "serial_number": found_device["serial_number"],
                    "firmware": found_device["firmware"],
                    "hardware": found_device["hardware"],
                    "status": found_device["status"],
                    "port": found_device["port"],


                }
                filtered_devices.append(device)
        case _:
            return Err("Es wurden mehr als zwei USB-CAN Geräte gefunden. Bitte stellen Sie sicher, dass Sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")

    return Ok(filtered_devices)


@app.get("/vga-step-1")
def vga_step_1(request: Request):
    data: Dict[str, Any] = {
        "request": request
    }
    return templates.TemplateResponse(name="vga_step_1.html", context=data)

# {'colordepth': 24,
#  'dpi': (158, 159),
#  'frequency': 60.01,
#  'id': 65,
#  'is_primary': True,
#  'orientation': <Orientation.ROTATE_0: 0>,
#  'position': Point(x=0, y=0),
#  'scale': (100.0, 100.0),
#  'size': Size(width=1920, height=1080),
#  'system_name': 'eDP-1',
#  'workarea': Rect(left=0, top=41, right=1920, bottom=1039)}


@app.get("/start-vga-check")
async def vga_check(request: Request):
    scan_result: Result[ScreenValue, str] = await check_vga_adapter()
    if scan_result.is_ok():
        result = scan_result.ok()
        pprint(result)
        data: Dict[str, Any] = {
            "request": request,
            "screen": result
        }
        return templates.TemplateResponse(name="vga_scan.html", context=data)
    elif scan_result.is_err():
        err = scan_result.unwrap_err()
        data_err: Dict[str, Any] = {
            "request": request,
            "error_message": err
        }
        return components.TemplateResponse(name="error.html", context=data_err)


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000, )


if __name__ == "__main__":
    main()
