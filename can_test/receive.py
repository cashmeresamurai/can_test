from pprint import pprint
from threading import Event
import can
import serial
import sys
import threading
import time
import base64
from PIL import Image
import io

from pathlib import Path

# Get the base directory (where pyproject.toml is)
BASE_DIR = Path(__file__).resolve().parent.parent

def receive_can_frames(port, bitrate, stop_event):
    """Receive CAN frames."""
    try:
        bus = can.interface.Bus(interface='slcan',
                                channel=f"{port}@3000000",
                                rtscts=True,
                                bitrate=bitrate)
    except serial.serialutil.SerialException as err:
        print(err)
        sys.exit(1)

    print("Ready to receive:")

    while not stop_event.is_set():
        try:
            msg = bus.recv(timeout=0.1)
            if msg is not None:
                # Bytes aus der CAN-Nachricht extrahieren
                bytes_received = bytes(list(msg.data))

                # Bytes in ein Bild umwandeln und speichern
                image = Image.open(io.BytesIO(bytes_received))
                image.save("received_image.jpg")
                print("Image saved as received_image.jpg")

                # Formatierte Ausgabe der CAN-Nachricht
                data = " ".join([f"{byte:02X}" for byte in msg.data])
                print(
                    f"ID: {msg.arbitration_id:X} [DLC: {msg.dlc}] Data: {data}")
            else:
                print("No message received")
        except can.CanError:
            print("CAN error occurred")
        except Exception as e:
            print(f"Error processing image: {e}")

    print("Shutting down CAN bus...")
    bus.shutdown()


def receive_image_over_can(port, bitrate, stop_event):
    try:
        bus = can.Bus(interface='slcan',
                      channel=f"{port}@3000000",
                      rtscts=True,
                      bitrate=bitrate)

        print("Bereit zum Empfangen des Bildes")
        collected_data = bytearray()
        bytes_received = 0
        expected_size = 3120  # Bekannte Bildgröße
        png_started = False

        # Konstruiere den korrekten Pfad für das Bild
        image_path = BASE_DIR / "can_test/static/received_colorbars.png"

        while not stop_event.is_set():
            msg = bus.recv(timeout=0.1)
            if msg is not None:
                if not png_started and len(msg.data) >= 8 and msg.data[0:8] == b'\x89PNG\r\n\x1a\n':
                    collected_data = bytearray()
                    bytes_received = 0
                    png_started = True
                    print("PNG Header erkannt - Starte Sammlung")

                if png_started:
                    collected_data.extend(msg.data)
                    bytes_received += len(msg.data)

                    if bytes_received % 400 == 0:
                        print(
                            f"Empfangen: {bytes_received}/{expected_size} Bytes")

                    if bytes_received >= expected_size:
                        try:
                            Image.open(io.BytesIO(collected_data)).verify()
                            with open(image_path, 'wb') as f:
                                f.write(collected_data)
                            print(
                                f"Bild erfolgreich gespeichert ({bytes_received} Bytes)")
                            collected_data = bytearray()
                            bytes_received = 0
                            png_started = False
                        except Exception as e:
                            print(f"Fehler beim Speichern: {e}")
                            collected_data = bytearray()
                            bytes_received = 0
                            png_started = False

    except Exception as e:
        print(f"Fehler beim Empfangen: {e}")
    finally:
        bus.shutdown()


def main():
    stop_event = Event()
    thread = threading.Thread(
        target=receive_can_frames,
        args=("/dev/ttyUSB0", 100000, stop_event)  # Korrigierte Syntax
    )
    thread.start()
    for seconds in range(1, 11):
        print(f"{seconds}/10 before set stop event signal")
        time.sleep(1)
    # Um die Schleife zu beenden
    stop_event.set()
    thread.join()


if __name__ == "__main__":
    main()
