# Pi Zero 2W BadUSB (Bookworm, 64-bit)

## Overview
This project transforms a Raspberry Pi Zero 2W (with Pi OS Lite, Bookworm, 64-bit) into a fully automated USB keyboard attack device—aka "BadUSB" or DIY USB Rubber Ducky. Plug it into a computer's USB port and your scripted keystrokes will execute with no user intervention!

---

## Features
- **Turn-key:** Just plug in—no SSH/monitor/keyboard needed
- **Modern:** Works with current Pi OS Bookworm (64-bit, kernel 6.x tested)
- **No external libraries:** Full in-project Python implementation, no `zero-hid` or `hid-gadget-test` needed
- **Custom payloads:** Easily script your own keyboard attacks in Ducky Script-inspired plain text
- **Robust:** Handles gadget setup/cleanup, boot automation via systemd

---

## Hardware Requirements
- Raspberry Pi Zero 2W
- microSD card (8GB+ recommended)
- USB data cable (must support data)
- Host PC (Windows/Linux/Mac)

---

## Initial Setup

1. **Install Pi OS Lite (Bookworm, 64-bit)** on SD card.
2. Edit `/boot/config.txt`: add at the end:
   ```
   dtoverlay=dwc2
   ```
3. Edit `/boot/cmdline.txt`: after `rootwait`:
   ```
   modules-load=dwc2
   ```
4. Boot the Pi Zero 2W.

---

## Project Directory Structure

```
/home/pi/pi-badusb/
├── gadget_setup.sh    # Clean/fresh USB gadget setup and teardown
├── autorun.sh         # Autoruns gadget + payload
├── run_payload.py     # Python runner for Ducky Script-style payloads
├── payload.txt        # Your script (plain text)
```
All scripts must be executable:
```bash
chmod +x gadget_setup.sh autorun.sh run_payload.py
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
4. To create your script, edit `payload.txt` as described below.

---

## Write Your Own Keyboard Automation Scripts—No Coding Needed!

Just edit `payload.txt` in the `pi-badusb` folder using the following commands—no programming needed! View file DUCKY_COMMANDS.md for a list of what you can do.

### Supported Commands:
- `REM ...`   (Comment, ignored)
- `DELAY ms`  (e.g. `DELAY 500` waits half a second)
- `STRING text` (Types the exact text)
- Basic actions: `ENTER`, `TAB`, `ESC`, `BACKSPACE`, `SPACE`, `F1-F12`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `HOME`, `END`, `INSERT`, `DELETE`, `PAGEUP`, `PAGEDOWN`
- Combo keys (space-separated, case-insensitive):
    - e.g. `CTRL ALT DEL`, `GUI r`, `CTRL SHIFT ESC`, `ALT F4`, `CTRL c`

### Example:
```
REM Launch Notepad and say hello!
GUI r
DELAY 200
STRING notepad
ENTER
DELAY 400
STRING Hello World from Pi Zero!
ENTER
```
Just edit the file and reboot or unplug and replug your Pi Zero 2W. **No Python or programming skills needed!**

---

## Example `run_payload.py` Implementation

```python
import time
import re

HID_DEVICE = '/dev/hidg0'

MODIFIERS = {
    'CTRL': 0x01,
    'SHIFT': 0x02,
    'ALT': 0x04,
    'GUI': 0x08,
    'CONTROL': 0x01,
    'WINDOWS': 0x08,
    'COMMAND': 0x08,
}

KEYS = {
    **{chr(i): (0x04 + i - ord('a'), 0) for i in range(ord('a'), ord('z')+1)},
    **{chr(i): (0x04 + i - ord('A'), MODIFIERS['SHIFT']) for i in range(ord('A'), ord('Z')+1)},
    **{str(n): (0x27 + n, 0) for n in range(1,10)},
    '0': (0x27, 0), ')': (0x27, MODIFIERS['SHIFT']), '!': (0x1e, MODIFIERS['SHIFT']), '@': (0x1f, MODIFIERS['SHIFT']),
    '#': (0x20, MODIFIERS['SHIFT']), '$': (0x21, MODIFIERS['SHIFT']), '%': (0x22, MODIFIERS['SHIFT']), '^': (0x23, MODIFIERS['SHIFT']),
    '&': (0x24, MODIFIERS['SHIFT']), '*': (0x25, MODIFIERS['SHIFT']), '(': (0x26, MODIFIERS['SHIFT']),
    '-': (0x2d, 0), '_': (0x2d, MODIFIERS['SHIFT']), '=': (0x2e, 0), '+': (0x2e, MODIFIERS['SHIFT']),
    '[': (0x2f, 0), '{': (0x2f, MODIFIERS['SHIFT']), ']': (0x30, 0), '}': (0x30, MODIFIERS['SHIFT']),
    '\': (0x31, 0), '|': (0x31, MODIFIERS['SHIFT']), ';': (0x33, 0), ':': (0x33, MODIFIERS['SHIFT']),
    "'": (0x34, 0), '"': (0x34, MODIFIERS['SHIFT']), '`': (0x35, 0), '~': (0x35, MODIFIERS['SHIFT']),
    ',': (0x36, 0), '<': (0x36, MODIFIERS['SHIFT']), '.': (0x37, 0), '>': (0x37, MODIFIERS['SHIFT']),
    '/': (0x38, 0), '?': (0x38, MODIFIERS['SHIFT']), ' ': (0x2c, 0), '	': (0x2b, 0),
    '
': (0x28, 0), '
': (0x28, 0), 'ENTER': (0x28, 0), 'RETURN': (0x28, 0),
    'ESC': (0x29, 0), 'ESCAPE': (0x29, 0), 'BACKSPACE': (0x2a, 0), 'TAB': (0x2b, 0),
    'SPACE': (0x2c, 0), 'CAPSLOCK': (0x39, 0),
    'F1': (0x3a, 0), 'F2': (0x3b, 0), 'F3': (0x3c, 0), 'F4': (0x3d, 0), 'F5': (0x3e, 0),
    'F6': (0x3f, 0), 'F7': (0x40, 0), 'F8': (0x41, 0), 'F9': (0x42, 0), 'F10': (0x43, 0), 'F11': (0x44, 0), 'F12': (0x45, 0),
    'PRINTSCREEN': (0x46, 0), 'SCROLLLOCK': (0x47, 0), 'PAUSE': (0x48, 0),
    'INSERT': (0x49, 0), 'HOME': (0x4a, 0), 'PAGEUP': (0x4b, 0), 'DELETE': (0x4c, 0), 'END': (0x4d, 0),
    'PAGEDOWN': (0x4e, 0), 'RIGHT': (0x4f, 0), 'LEFT': (0x50, 0), 'DOWN': (0x51, 0), 'UP': (0x52, 0),
    'DEL': (0x4c, 0),
}

def send_hid(mod, key):
    report = bytes([mod, 0x00, key, 0x00, 0x00, 0x00, 0x00, 0x00])
    with open(HID_DEVICE, 'wb') as hid:
        hid.write(report)
        hid.flush()
        hid.write(b'
