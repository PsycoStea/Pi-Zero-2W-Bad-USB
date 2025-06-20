# Pi Zero 2W BadUSB (Bookworm, 64-bit)

## Overview
This project transforms a Raspberry Pi Zero 2W (with Pi OS Lite, Bookworm, 64-bit) into a fully automated USB keyboard attack device—aka "BadUSB" or DIY USB Rubber Ducky. Plug it into a computer's USB port and your scripted keystrokes will execute with no user intervention!

## Features
- **Turn-key:** Just plug in—no SSH/monitor/keyboard needed
- **Modern:** Works with current Pi OS Bookworm (64-bit, kernel 6.x tested)
- **From scratch:** No external Python HID packages or outdated guides used
- **Custom payloads:** Easily script your own keyboard attacks in Python
- **Robust:** Handles gadget setup/cleanup, tested for systemd boot automation

## Hardware Requirements
- **Raspberry Pi Zero 2W**
- **microSD card** (8GB+ recommended)
- **USB data cable** (must be able to do data, not just charging)
- **Host PC** (Windows, Linux, or Mac for testing)

## Initial Pi Preparation
1. **Flash Pi OS Lite (Bookworm, 64-bit)** to your SD card.
2. Edit `/boot/config.txt`: add at the end
   ```
   dtoverlay=dwc2
   ```
3. Edit `/boot/cmdline.txt`: right after `rootwait` (do not split lines!), add:
   ```
   modules-load=dwc2
   ```

## Project File Layout
```
/home/pi/pi-badusb/
├── gadget_setup.sh    # Clean/fresh USB gadget setup and teardown
├── autorun.sh         # Autoruns gadget + payload
├── type_string.py     # Example: auto-types "Hello World"
```
All scripts must be executable:
```bash
chmod +x gadget_setup.sh autorun.sh type_string.py
```

---

## Setup Instructions

1. **Copy all scripts** to `/home/pi/pi-badusb/` on your Pi.

2. **Create the systemd service:**
   Create `/etc/systemd/system/pi-badusb.service` with:
   ```
   [Unit]
   Description=Pi Zero 2W BadUSB Startup Payload
   After=multi-user.target

   [Service]
   Type=simple
   ExecStart=/home/pi/pi-badusb/autorun.sh
   ExecStop=/bin/bash -c 'echo "" | tee /sys/kernel/config/usb_gadget/g1/UDC'
   RemainAfterExit=yes
   User=root

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable pi-badusb.service
   sudo systemctl start pi-badusb.service
   ```

---

## Usage
1. Power off your Pi Zero 2W.
2. Plug the Pi’s USB “data” port into the target PC using a data-capable USB cable.
3. Wait ~10 seconds—the gadget will set up and the payload (keystrokes) will execute automatically!
4. To change what is typed, edit `type_string.py`.

---

## Example Payload (type_string.py)
```python
import time

HID_DEVICE = "/dev/hidg0"
MOD_NONE = 0x00
MOD_LSHIFT = 0x02
ASCII_TO_HID = {
    'a': (0x04, MOD_NONE), 'b': (0x05, MOD_NONE), # ...and so on
    'A': (0x04, MOD_LSHIFT), # ...etc, full table in project
    ' ': (0x2C, MOD_NONE), '
': (0x28, MOD_NONE)
}
def send_key(hid, keycode, modifier):
    report = bytes([modifier, 0x00, keycode, 0x00, 0x00, 0x00, 0x00, 0x00])
    hid.write(report)
    hid.flush()
    hid.write(b'
