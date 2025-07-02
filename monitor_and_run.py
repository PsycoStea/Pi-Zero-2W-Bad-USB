import os
import time
import subprocess

HID_DEVICE = '/dev/hidg0'
PAYLOAD_SCRIPT = '/home/pi/pi-badusb/run_payload.py'
RELOAD_GADGET_SCRIPT = '/home/pi/pi-badusb/reload_gadget.sh'

def wait_for_writable_hidg(hid_device_path):
    print("BadUSB: Waiting for host (PC) USB connection...")
    while True:
        if os.path.exists(hid_device_path):
            try:
                with open(hid_device_path, 'wb', buffering=0) as hid:
                    try:
                        hid.write(b'\x00' * 8)
                        hid.flush()
                        return
                    except Exception:
                        pass
            except Exception:
                pass
        time.sleep(0.3)

while True:
    wait_for_writable_hidg(HID_DEVICE)
    print("\nHost detected! Running payload...\n")
    subprocess.run(["python3", PAYLOAD_SCRIPT])
    print("Payload finished. Waiting for disconnect...")

    # Wait for /dev/hidg0 to disappear (host unplugged/disconnected)
    while os.path.exists(HID_DEVICE):
        time.sleep(0.3)
    print("Host disconnected. Reloading gadget...")

    # Unbind/rebind gadget for next plug-in!
    subprocess.run(["bash", RELOAD_GADGET_SCRIPT])
    print("Gadget reloaded, waiting for the next connection.\n")
