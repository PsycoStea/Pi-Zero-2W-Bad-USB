# Pi Zero 2W BadUSB (Bookworm, 64-bit)

## Overview
Transform a Raspberry Pi Zero 2W (Pi OS Lite 64-bit, Bookworm) into an automated USB keyboard attack platform—just plug it into a computer's USB data port and it launches your scripted keystrokes using user-friendly Ducky Script commands. No Python knowledge needed!

## Features
- Turn-key and easy: edit a text payload, plug in, and go
- Ducky Script-style scripting for non-coders
- Modern: works with Pi OS Lite Bookworm 64-bit, kernel 6.x+
- Robust: all key mappings, systemd service, and error handling included

---

## Hardware Requirements
- Raspberry Pi Zero 2W
- microSD card (8GB+)
- Data-capable USB cable
- Host computer (Windows, Linux, Mac)

---

## Quick Setup

1. **Prepare your Pi**
   - Flash Pi OS Lite (Bookworm, 64-bit)
   - Edit `/boot/config.txt` to add:
     ```
     dtoverlay=dwc2
     ```
   - Edit `/boot/cmdline.txt` after `rootwait` (all one line!):
     ```
     modules-load=dwc2
     ```
2. **Copy repo to `/home/pi/pi-badusb/`**
3. **Make all scripts executable:**
   ```bash
   chmod +x gadget_setup.sh autorun.sh run_payload.py
   ```
4. **Create the systemd service:**
   `/etc/systemd/system/pi-badusb.service`:
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
   Enable with:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable pi-badusb.service
   sudo systemctl start pi-badusb.service
   ```

---

## Usage
1. Power off your Pi
2. Plug Pi’s USB data port (**not PWR**) into your target machine
3. Wait 5–10 seconds for the payload to run
4. Edit `payload.txt` to change the attack (just unplug and replug the Pi to use new scripts)

---

## Write Your Own Payloads—No Code Needed

Write or edit `/home/pi/pi-badusb/payload.txt` using these commands:

- `REM ...`             Comment line
- `DELAY ms`            Pause (ms)
- `STRING text`         Types the text
- `ENTER`, `TAB`, `ESC`, `BACKSPACE`, `SPACE` etc.
- Arrow keys: `UP`, `DOWN`, `LEFT`, `RIGHT`
- Navigation: `HOME`, `END`, `INSERT`, `DELETE`, `PAGEUP`, `PAGEDOWN`
- F1–F12
- Modifier combos: `CTRL`, `ALT`, `SHIFT`, `GUI` (Win/Cmd), e.g. `CTRL c`, `GUI r`, `CTRL SHIFT ESC`, `ALT TAB`

**Example:**
```
REM Launch Notepad and type Hello World!
GUI r
DELAY 500
STRING notepad
ENTER
DELAY 800
STRING Hello World from Pi Zero!
ENTER
```
For a full command reference see [`DUCKY_COMMANDS.md`](./DUCKY_COMMANDS.md).

---

## Troubleshooting
- No typing? Ensure a data USB cable and correct port
- Service fails? Check `sudo systemctl status pi-badusb.service`
- Numbers or keys not working? Pull latest version and check `run_payload.py`
- BrokenPipeError? Confirm the Pi is plugged into a host and `/dev/hidg0` exists

---

## ⚠️ Legal Notice ⚠️
> For educational/authorised testing only. Never use on devices you don't own or have explicit permission to test.

---

## Credits & Contributing
- PsycoStea ❤️
- Original Ducky Script by Hak5; inspired by many in the Pi/infosec community.
- PRs and issues welcome! Improvements and payloads encouraged.
