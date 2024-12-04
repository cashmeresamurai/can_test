from typing import Any, TypedDict
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
from scanner import FoundDevice, FoundDeviceError, initialize
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
pruefhilfsmittel = None
pruefgeraet = None


class TestDevice(TypedDict):
    name: str
    port: str


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
    except:
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

        # if send_thread and send_thread.is_alive():
        #     return {
        #         "success": False,
        #         "message": "Senden läuft bereits"
        #     }

        send_stop_event = Event()
        send_thread = threading.Thread(
            target=send_image_over_can,
            args=(test_device["port"], 100000, send_stop_event)
        )
        send_thread.start()
        return Ok(True)
    except:
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
def send_receive_1():

    pass

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


@app.get("/start-scan", response_class=HTMLResponse)
async def start_scan(request: Request):
    initialize_result: Result[Dict[str, Any], str] = initialize()
    # print(initialize_result)
    if isinstance(initialize_result, Err):
        error_message: str = initialize_result.unwrap_err()
        data: Dict[str, Any] = {
            "request": request,
            "error_message": error_message
        }

        return templates.TemplateResponse(
            name="components/error.html",
            context=data,
        )
    elif isinstance(initialize_result, Ok):
        untyped_devices: Dict[str, Any] = initialize_result.ok()
        devices_result: List[Dict[str, str]] = untyped_devices["devices"]
        typed_device_list: List[Device] = []
        for device in devices_result:
            device_result = device.unwrap()
            typed_device: Device = {
                "serial_number": device_result["serial_number"],
                "hardware": device_result["hardware"],
                "firmware": device_result["firmware"],
                "status": device_result["status"]
            }
            typed_device_list.append(typed_device)

        devices: Result[List[Device], str] = filter_devices(
            devices=typed_device_list)
        if devices.is_err():
            error_message1: str = devices.unwrap_err()
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
        # raise HTTPException(status_code=500, detail=str(e))


class Device(TypedDict):
    serial_number: str
    firmware: str
    hardware: str
    status: str
    device_type: str


def filter_devices(devices: List[Device]) -> Result[List[Device], str]:
    global pruefhilfsmittel, pruefgeraet
    filtered_devices: List[Device] = []
    match len(devices):
        case 0:
            return Err("Es wurden keine USB-CAN Geräte gefunden. Bitte stellen Sie sicher, dass sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")
        case 1:
            return Err("Es wurde ein USB-CAN Gerät gefunden. Bitte stellen Sie sicher, dass Sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")
        case 2:
            for found_device in devices:
                # device_type = "Prüfhilfsmittel" if found_device[
                #     "serial_number"] == "380105787" else "Prüfgerät"
                if found_device["serial_number"] == "380105787":
                    pruefhilfsmittel: TestDevice = {
                        "name": "Prüfhilfsmittel",
                        "port": found_device["port"]
                    }
                device: Device = {
                    "serial_number": found_device["serial_number"],
                    "firmware": found_device["firmware"],
                    "hardware": found_device["hardware"],
                    "status": found_device["status"],
                    "device_type": device_type
                }
                filtered_devices.append(device)
        case _:
            return Err("Es wurden mehr als zwei USB-CAN Geräte gefunden. Bitte stellen Sie sicher, dass Sie die Anweisungen richtig befolgt haben und starten sie den Test erneut.")

    return Ok(filtered_devices)


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
