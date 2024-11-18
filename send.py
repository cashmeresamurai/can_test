from threading import Event
import can
import serial
import sys
import threading
import time


def send_can_frames(port, bitrate, stop_event):
    """Send CAN frames."""
    try:
        bus = can.interface.Bus(
            interface='slcan',
            channel=f"{port}@3000000",
            rtscts=True,
            bitrate=bitrate
        )
    except serial.serialutil.SerialException as err:
        print(f"Fehler beim Öffnen des CAN-Bus: {err}")
        return

    print(f"Sende auf {port}")

    msg = can.Message(
        arbitration_id=0x100,
        is_extended_id=False,
        data=[0x00, 0x01, 0x02, 0x03]
    )

    while not stop_event.is_set():
        try:
            bus.send(msg)
            time.sleep(0.5)
        except can.CanError:
            pass

    print("Beende CAN-Bus...")
    bus.shutdown()
