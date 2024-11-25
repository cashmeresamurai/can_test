from threading import Event
import can
import serial
import sys
import threading
import time
from PIL import Image
import io


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


def send_image_over_can(port, bitrate, stop_event, image_path="colorbars.png"):
    try:
        bus = can.interface.Bus(
            interface='slcan',
            channel=f"{port}@3000000",
            rtscts=True,
            bitrate=bitrate
        )

        with Image.open(image_path) as img:
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            image_bytes = img_byte_array.getvalue()

        chunks = [image_bytes[i:i+8] for i in range(0, len(image_bytes), 8)]
        total_frames = len(chunks)
        print(f"Gesamtgröße: {len(image_bytes)} Bytes")
        print(f"Starte Übertragung von {total_frames} Frames")

        frames_sent = 0
        start_time = time.time()

        while not stop_event.is_set():
            for i, chunk in enumerate(chunks):
                if len(chunk) < 8:
                    chunk = chunk + bytes(8 - len(chunk))

                msg = can.Message(
                    arbitration_id=0x100,
                    is_extended_id=False,
                    data=chunk
                )
                bus.send(msg)
                frames_sent += 1

                if frames_sent % 50 == 0:  # Status alle 50 Frames
                    elapsed = time.time() - start_time
                    print(
                        f"Gesendet: {frames_sent}/{total_frames} Frames ({(frames_sent/total_frames*100):.1f}%) in {elapsed:.1f}s")

                time.sleep(0.001)  # 1ms Pause zwischen Frames

            print(
                f"Übertragung abgeschlossen nach {time.time() - start_time:.1f} Sekunden")
            break  # Beende nach einem kompletten Durchlauf

    except Exception as e:
        print(f"Fehler beim Senden: {e}")
    finally:
        bus.shutdown()
