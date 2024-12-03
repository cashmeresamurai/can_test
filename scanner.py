#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

"""
CAN device tester.
"""

from typing import Dict, Any, List
from typing_extensions import TypedDict
from result import Result, Ok, Err

import argparse
import os.path
import queue
import socket
import sys
import textwrap
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from subprocess import PIPE, Popen

import can
import serial
import serial.tools.list_ports

import netifaces

VSCAN_OK = b'\r'
VSCAN_KO = b'\x07'
MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900

EXAMPLES = ('''\
            Examples
            --------
            Find all USB-CAN Plus devices:
                python3 vscantester.py
            Check a device behind /dev/ttyUSB0:
                python3 vscantester.py /dev/ttyUSB0
            Find all NetCAN Plus devices:
                python3 vscantester.py -u
            Receive CAN frames at 100000b/s:
                python3 vscantester.py -r -b 100000 /dev/ttyUSB0
            Send a single CAN frame at 100000b/s:
                python3 vscantester.py -t single -b 100000 /dev/ttyUSB0
            Send the same CAN frame continuously at 100000b/s:
                python3 vscantester.py -t same -b 100000 /dev/ttyUSB0
            Send a CAN frame continuously with incrementing last data byte at 100000b/s:
                python3 vscantester.py -t inc -b 100000 /dev/ttyUSB0
            ''')


class SsdpListener(threading.Thread):
    """SSDP listener."""

    def __init__(self, iface, dev_queue):
        threading.Thread.__init__(self)
        self.iface = iface
        self.dev_queue = dev_queue
        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_DGRAM,
                                  socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET,
                             socket.SO_REUSEADDR, 1)

    def bind(self):
        """Bind to specified interface and multicast group."""
        self.sock.bind(('', MCAST_PORT))
        mreq = socket.inet_aton(
            MCAST_GRP) + socket.inet_aton(self.iface)
        self.sock.setsockopt(socket.IPPROTO_IP,
                             socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.settimeout(10)
        self.sock.setsockopt(socket.IPPROTO_IP,
                             socket.IP_MULTICAST_IF,
                             socket.inet_aton(self.iface))

    def get_xml_tag(self, child, tag):
        """Get XML tag from device description."""
        for item in child:
            if item.tag == tag:
                return item.text

    def parse_xml(self, text):
        """Extract freindlyName and check if it is NET-CAN."""
        dev = dict()
        root = ET.fromstring(text)
        for child in root:
            if child.tag == "{urn:schemas-upnp-org:device-1-0}device":
                for item in child:
                    if item.tag == "{urn:schemas-upnp-org:device-1-0}friendlyName":
                        if "NET-CAN" in item.text:
                            dev['model'] = self.get_xml_tag(
                                child, "{urn:schemas-upnp-org:device-1-0}modelName")
                            dev['fw'] = self.get_xml_tag(
                                child, "{urn:schemas-upnp-org:device-1-0}firmWareVersionNumber")
                            dev['hw'] = self.get_xml_tag(
                                child, "{urn:schemas-upnp-org:device-1-0}hardWareVersionNumber")
                            dev['sernum'] = self.get_xml_tag(
                                child, "{urn:schemas-upnp-org:device-1-0}serialNumber")
                            return dev

        return None

    def run(self):
        """Watch for SSDP messages."""
        self.bind()
        while True:
            try:
                buf, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            if b"devinfo.xml" in buf:
                location_idx = buf.find(b"LOCATION:")
                location_end_idx = buf.find(b"xml", location_idx)
                url = buf[location_idx + 9:location_end_idx + 3]
                response = urllib.request.urlopen(url.decode("utf-8"))
                data = response.read()
                text = data.decode('utf-8')
                dev = self.parse_xml(text)
                if dev:
                    dev['ip'] = addr[0]
                    self.dev_queue.put(dev)


class UsbCan(object):
    """USB-CAN Plus class."""

    def __init__(self, port):
        self.port = port
        self.ser_port = None

    def close(self):
        """Close serial port."""
        self.ser_port.close()

    def init_serial_port(self):
        """Initialize serial port."""
        ret = True
        try:
            self.ser_port = serial.serial_for_url(self.port,
                                                  baudrate=3000000,
                                                  timeout=1,
                                                  rtscts=True)
        except serial.serialutil.SerialException as err:
            print(err)
            ret = False
        except BrokenPipeError as err:
            print(err)
            ret = False

        return ret

    def close_can_channel(self):
        """Send 'C' to close the CAN channel."""
        try:
            self.ser_port.write("C\r".encode('ascii'))
        except serial.serialutil.SerialException as err:
            print(err)
            return False

        try:
            buf = self.ser_port.read(1)
        except serial.serialutil.SerialException as err:
            print(err)
            return False

        if buf != VSCAN_KO and buf != VSCAN_OK:
            return False

        return True

    def lsof(self):
        """Check if a port is already open."""
        proc = Popen(["lsof"], stdout=PIPE, stderr=PIPE)
        output = proc.communicate()[0]
        for line in output.decode('ascii').split('\n'):
            if line.find(self.port) != -1:
                print(f"{self.port} is already open:\n{line}")

    def get_serial_number(self):
        """Send 'N' to get the serial number."""
        ser_num = None
        try:
            self.ser_port.write("N\r".encode('ascii'))
        except serial.serialutil.SerialException as err:
            print(err)
            return ser_num

        buf = self.ser_port.read(12)
        if buf[0] != 78:
            print(f"Wrong first character: {buf[0]}")
            return ser_num

        if buf[len(buf) - 1] != 13:
            print(f"Wrong last character: {buf[len(buf) - 1]}")
            return ser_num

        return buf[1:len(buf) - 2]

    def get_version_info(self):
        """Send 'V' to get the firmware version."""
        ver = None
        try:
            self.ser_port.write("V\r".encode('ascii'))
        except serial.serialutil.SerialException as err:
            print(err)
            return ver

        buf = self.ser_port.read(6)
        if buf[0] != 86:
            print(f"Wrong first character: {buf[0]}")
            return ver

        if buf[len(buf) - 1] != 13:
            print(f"Wrong last character: {buf[len(buf) - 1]}")
            return ver

        return buf[1:len(buf) - 1]


def original_find_all_usb_can_devices():
    """Find all serial ports with FT-X chip."""
    port_list = []
    ports = serial.tools.list_ports.grep("0403:6015")
    for item in ports:
        port_list.append(item.device)

    return port_list


def find_port(port):
    """Find serial port in the list."""
    ports = serial.tools.list_ports.grep(port)
    for item in ports:
        if item.device == port:
            print(f"Serial port found: {item}")
            if item.description.find('USB-CAN Plus') != -1:
                print("This device has a correct description")
            else:
                print(f"Device description is wrong: {item.description}")


def check_lsmod(driver):
    """Invoke lsmod and check for ftdi_sio driver."""
    proc = Popen(["lsmod"], stdout=PIPE, stderr=PIPE)
    output = proc.communicate()[0]
    for line in output.decode('ascii').split('\n'):
        if driver in line:
            return True

    return False


def find_file(path, drv_file_name):
    """Find file."""
    for root, dirs, files in os.walk(path):
        if drv_file_name in files:
            return os.path.join(root, drv_file_name)

    return None


def find_driver(kernel_ver, drv_name):
    """Check whether slcan is available on the system."""
    drv_info = {'loaded': False, 'state': 'na'}

    if check_lsmod(drv_name):
        drv_info['loaded'] = True

    # check if the driver is in rootfs
    drv_path = find_file(f"/lib/modules/{kernel_ver}/kernel/drivers",
                         f"{drv_name}.ko")
    if drv_path:
        drv_info['state'] = 'module'
        drv_info['path'] = drv_path
        return drv_info

    # check if the driver is builtin
    with open(f"/lib/modules/{kernel_ver}/modules.builtin", "r") as mods:
        for line in mods:
            if f"{drv_name}.ko" in line:
                drv_info['state'] = 'builtin'
                break

    return drv_info


def fix_port_type(port):
    """
    If a port is an IP address with a port number,
    convert it to socket://...
    """
    tmp_port = port
    if ":" in port:
        tmp_port = f"socket://{port}"

    return tmp_port


def ssdp_discover():
    """Discover NetCAN Plus devices."""
    dev_queue = queue.Queue()
    ssdp_listeners = []
    netcans = []
    ifs = netifaces.interfaces()
    for item in ifs:
        addrs = netifaces.ifaddresses(item)
        try:
            ssdp_item = SsdpListener(addrs[netifaces.AF_INET][0]["addr"],
                                     dev_queue)
            ssdp_item.start()
            ssdp_listeners.append(ssdp_item)
        except KeyError:
            pass

    print(f"{len(ssdp_listeners)} SSDP threads started.")
    t_end = time.time() + 10
    while time.time() < t_end:
        try:
            msg = dev_queue.get(block=True, timeout=0.1)
        except queue.Empty:
            continue
        if msg not in netcans:
            netcans.append(msg)
            print(f"NetCAN {msg['model']}({msg['ip']}) -> "
                  f"(SN: {msg['sernum']}, FW: {msg['fw']}, HW: {msg['hw']})")


def show_driver_info(drv_name, drv_info):
    """Show driver information."""
    if drv_info['state'] == 'na':
        print(f"{drv_name}.ko not found on the system")
    elif drv_info['state'] == 'builtin':
        print(f"{drv_name}.ko is builtin")
    else:
        if drv_info['loaded']:
            print(f"{drv_name}.ko is a module and is loaded")
            print(drv_info['path'])
        else:
            print(f"{drv_name}.ko is a module and is not loaded")
            print(drv_info['path'])


def get_system_info():
    """Get system information."""
    # get kernel version
    proc = Popen(["uname", "-r"], stdout=PIPE, stderr=PIPE)
    output = proc.communicate()[0]
    kernel_ver = output.decode('ascii').split('\n')[0]

    print(f"Kernel: {kernel_ver}")

    drv_info = find_driver(kernel_ver, "ftdi_sio")
    show_driver_info("ftdi_sio", drv_info)

    drv_info = find_driver(kernel_ver, "slcan")
    show_driver_info("slcan", drv_info)


def receive_can_frames(port, bitrate):
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

    while True:
        msg = bus.recv()
        data = "".join("{:02X} ".format(byte) for byte in msg.data)
        print("{:X} [{}] {}".format(msg.arbitration_id,
                                    msg.dlc,
                                    data))

    bus.shutdown()


def send_can_frames(port, bitrate, mode):
    """Send CAN frames."""
    try:
        bus = can.interface.Bus(interface='slcan',
                                channel=f"{port}@3000000",
                                rtscts=True,
                                bitrate=bitrate)
    except serial.serialutil.SerialException as err:
        print(err)
        sys.exit(1)

    if mode == 'single':
        print("Sending a single CAN frame")
        msg = can.Message(arbitration_id=0x100,
                          is_extended_id=False,
                          data=[0x00, 0x01, 0x02, 0x03])
        bus.send(msg)
    elif mode == 'same':
        print("Sending the same CAN frame every 500ms")
        msg = can.Message(arbitration_id=0x100,
                          is_extended_id=False,
                          data=[0x00, 0x01, 0x02, 0x03])
        while True:
            bus.send(msg)
            time.sleep(0.5)
    elif mode == 'inc':
        print("Sending a CAN frame with incrementing last byte every 500ms")
        msg = can.Message(arbitration_id=0x100,
                          is_extended_id=False,
                          data=[0x00, 0x01, 0x02, 0x03])
        while True:
            if msg.data[3] == 0xff:
                msg.data[3] = 0
            else:
                msg.data[3] = msg.data[3] + 1
            bus.send(msg)
            time.sleep(0.5)


class FoundDeviceError(TypedDict):
    port: str
    status: str
    error: str


def initialize() -> Result[Dict[str, Any], str]:
    """Main routine."""
    port_list_result: Result[List["str"], str] = find_all_usb_can_devices()
    print(port_list_result)
    if isinstance(port_list_result, Err):
        return Err("Failed to find USB-CAN devices")

    port_list = port_list_result
    if not port_list:
        if sys.platform.startswith('linux'):
            get_system_info()
        return Err("No USB-CAN devices found")

    devices_info: List[Result[FoundDevice, FoundDeviceError]] = []
    for device in port_list.unwrap():
        device_result: Result[FoundDevice, str] = process_device(device)
        if isinstance(device_result, Ok):
            found_device: FoundDevice = device_result.unwrap()
            devices_info.append(Ok(found_device))
        elif device_result.is_err():
            error_message: str = device_result.unwrap_err()
            device_error: FoundDeviceError = {
                "port": device,
                "status": "error",
                "error": error_message
            }
            devices_info.append(Err(device_error))
        # match device_result:
        #     case isinstance(devices_info, Ok):
        #         devices_info[device] = info
            # case Err(error):
            #     devices_info[str(item)] = {
            #         'port': str(item),
            #         'status': 'error',
            #         'error': str(error)
            #     }

    return Ok({"status": "success", "devices": devices_info})


class FoundDevice(TypedDict):
    # 'serial_number': ser_num.decode('ascii'),
    serial_number: str
    # 'firmware': f"{ver_major}:{ver_minor}",
    firmware: str
    # 'hardware': f"{hw_major}:{hw_minor}",
    hardware: str
    # 'status': 'success'
    status: str


def process_device(device_port: str) -> Result[FoundDevice, str]:
    """Process a single USB-CAN device."""

    usbcan = UsbCan(device_port)

    init_result = usbcan.init_serial_port()
    if not init_result:
        return Err("Failed to open serial port")

    close_result = usbcan.close_can_channel()
    if not close_result:
        return Err("Failed to close the CAN channel")

    ser_num = usbcan.get_serial_number()
    if not ser_num:
        return Err("Failed to get the serial number")

    ver = usbcan.get_version_info()
    if not ver:
        return Err("Failed to get the firmware version")

    try:
        ver_major = int(ver[2:3], 16)
        ver_minor = int(ver[3:], 16)
        hw_major = int(ver[:1], 16)
        hw_minor = int(ver[1:2], 16)
    except (ValueError, IndexError):
        return Err("Failed to parse version information")

    found_device: FoundDevice = {
        'serial_number': ser_num.decode('ascii'),
        'firmware': f"{ver_major}:{ver_minor}",
        'hardware': f"{hw_major}:{hw_minor}",
        'status': 'success'
    }

    usbcan.close()
    return Ok(found_device)


def find_all_usb_can_devices() -> Result[List[str], str]:
    """Find all USB-CAN devices and return as Result."""
    try:
        devices = original_find_all_usb_can_devices()
        match len(devices):
            case 0:
                return Err("No devices found")
            case _:
                return Ok(devices)
        # return Ok(devices) if devices is not None else Err("No devices found")
    except Exception as e:
        return Err(f"Failed to find USB-CAN devices: {str(e)}")

# Hilfsfunktion für das Finden von USB-CAN Geräten


if __name__ == "__main__":
    initialize()


def main():
    """main routine."""
    parser = argparse.ArgumentParser(description='VSCAN device tester',
                                     usage=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(EXAMPLES))
    parser.add_argument("-u", "--upnp",
                        help="Perform UPnP/SSDP search",
                        action='store_true')
    parser.add_argument("-r", "--rx",
                        help="Receive CAN messages",
                        action='store_true')
    parser.add_argument("-b", "--bitrate",
                        help="CAN bitrate",
                        type=int,
                        default=1000000)
    parser.add_argument("-tx", "--tx",
                        help="Transmit CAN frame(s) mode",
                        choices=['single', 'same', 'inc'],
                        default=None)
    if sys.platform.startswith('linux'):
        parser.add_argument("-s", "--system",
                            help="Get system information (Linux only)",
                            action='store_true')
    parser.add_argument("port",
                        nargs="?",
                        default="all",
                        action="store",
                        help="Serial port name. If omitted, the tool "
                             "will search for all available devices")
    try:
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        raise

    if args.upnp:
        ssdp_discover()
        os._exit(0)

    if sys.platform.startswith('linux'):
        if args.system:
            get_system_info()
            sys.exit(0)

    port_list = []
    if args.port == 'all':
        port_list = find_all_usb_can_devices()
        if not port_list:
            print("No USB-CAN devices found")
            if sys.platform.startswith('linux'):
                get_system_info()
    else:
        port_list.append(fix_port_type(args.port))

    if args.rx:
        if args.port == 'all':
            print("Please specify a port")
            sys.exit(1)
        else:
            receive_can_frames(fix_port_type(args.port), args.bitrate)

    if args.tx:
        if args.port == 'all':
            print("Please specify a port")
            sys.exit(1)
        else:
            send_can_frames(fix_port_type(args.port), args.bitrate, args.tx)
            sys.exit(0)

    for item in port_list:
        usbcan = UsbCan(item)
        if sys.platform.startswith('linux'):
            find_port(usbcan.port)
            usbcan.lsof()

        if not usbcan.init_serial_port():
            print("Failed to open serial port")
            sys.exit(1)

        if not usbcan.close_can_channel():
            print("Failed to close the CAN channel")
            print("The port could be opened but this "
                  "device doesn't respond to the ASCII commands")
            sys.exit(1)

        ser_num = usbcan.get_serial_number()
        if not ser_num:
            print("Failed to get the serial number")
            sys.exit(1)

        ver = usbcan.get_version_info()
        if not ver:
            print("Failed to get the firmware version")
            sys.exit(1)

        ver_major = int(ver[2:3], 16)
        ver_minor = int(ver[3:], 16)
        hw_major = int(ver[:1], 16)
        hw_minor = int(ver[1:2], 16)
        print(f"Found VSCAN device with the following info:")
        print(f"{usbcan.port} -> (SN: {ser_num.decode('ascii')}, "
              f"FW: {ver_major}:{ver_minor}, "
              f"HW: {hw_major}:{hw_minor})")

        usbcan.close()


# if __name__ == '__main__':
#     main()
