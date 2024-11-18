from threading import Event
import can
import serial
import sys
import threading
import time


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
            # Timeout von 0.1 Sekunden hinzugefügt
            msg = bus.recv(timeout=0.1)
            if msg is not None:
                data = "".join("{:02X} ".format(byte) for byte in msg.data)
                print("{:X} [{}] {}".format(msg.arbitration_id,
                                            msg.dlc,
                                            data))
        except can.CanError:
            pass

    print("Shutting down CAN bus...")
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
