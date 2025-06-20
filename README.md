# Pi Zero 2W BadUSB (Bookworm, 64-bit)

## Overview
Transform your Raspberry Pi Zero 2W into a fully automated USB keyboard payload delivery device running Ducky Script! Includes customizable LED blink feedback for non-coders and a modern Pi OS Bookworm 64-bit setup.

---

## Features
- Plug-and-play keystroke script execution at boot or on USB connect
- Payloads written in easy Ducky Script (non-coders welcome)
- Fully adjustable typing/combo/ENTER speed at the top of the script
- Customizable ACT LED blinking pattern at payload completion
- Works on Pi OS Bookworm 64-bit for Pi Zero 2W (kernel 6.x tested)

---

## Hardware Requirements
- Raspberry Pi Zero 2W
- microSD card (8GB+)
- USB data cable (not just charging cable)
- Host PC for testing (Windows, Linux, Mac)
- (Optional) Breadboard button for GPIO triggering (advanced)

---

## 1. Pi OS Setup and Prerequisites

1. **Flash Pi OS Lite (Bookworm, 64-bit) to your SD card.**

2. **Edit `/boot/config.txt`:**
    Add to the end:
    ```
    dtoverlay=dwc2
    ```

3. **Edit `/boot/cmdline.txt`:**
    After `rootwait` (all one line!), add:
    ```
    modules-load=dwc2
    ```

4. Boot your Pi, then clone/copy this repository to `/home/pi/pi-badusb/`.
   
5. Make scripts executable:
    ```bash
    chmod +x gadget_setup.sh autorun.sh run_payload.py monitor_and_run.py reload_gadget.sh
    ```

---

## 2. Systemd Service Setup

1. Create `/etc/systemd/system/pi-badusb.service` with:
    
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

2. Enable the service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable pi-badusb.service
    sudo systemctl start pi-badusb.service
    ```

---

## 3. Script & Payload Execution

- **At boot or USB connection:** The Pi executes any payload found in `payload.txt`.
- **Script typing speed** and **LED blinking** are user-adjustable by editing constants at the top of `run_payload.py`:

    ```python
    # Delay between individual keys/typing
    KEY_DELAY = 0.01        # (seconds, default: 0.01 = 10ms)
    COMBO_DELAY = 0.02      # (after modifier/combo keys)
    ENTER_DELAY = 0.03      # (after pressing ENTER)

    # Wait before LED blink feedback starts after payload
    POST_PAYLOAD_BLINK_WAIT = 1.0  # (seconds)

    # LED Blink pattern: list of (on_time, off_time), e.g. 5 blinks fast:
    BLINK_PATTERN = [(0.1, 0.1)] * 5
    ```

---

## 4. Ducky Script Payloads (No Coding Needed)

Edit `payload.txt` using these simple commands (one per line):

- `REM ...`           — Comment
- `DELAY ms`          — Pause (ms)
- `STRING text`       — Types the text
- Basic keys: `ENTER`, `TAB`, `ESC`, `BACKSPACE`, `SPACE`, etc.
- Arrows: `UP`, `DOWN`, `LEFT`, `RIGHT`
- Navigation: `HOME`, `END`, `INSERT`, `DELETE`, `PAGEUP`, `PAGEDOWN`
- F1–F12
- Combo keys: `CTRL`, `ALT`, `SHIFT`, `GUI` (Win/Cmd), e.g. `CTRL c`, `GUI r`, `ALT F4`, `CTRL SHIFT ESC`

**Example payload:**
```
REM Launch Notepad and type Hello World!
GUI r
DELAY 500
STRING notepad
ENTER
DELAY 800
STRING Hello from Pi Zero 2W!
ENTER
```
See `DUCKY_COMMANDS.md` for a full command list.

---

## 5. LED Blink Customization

- The green ACT LED blinks a pattern after payload runs.
- Blink settings are set at the top of `run_payload.py`:

    ```python
    BLINK_PATTERN = [(0.2, 0.2)] * 10           # 10 moderate blinks
    # BLINK_PATTERN = [(0.3, 0.1)]*3 + [(0.1,0.1)]*3   # Morse: 3 long, 3 short
    POST_PAYLOAD_BLINK_WAIT = 1.0               # Wait (s) before blinking
    ```
- LED always ends ON after script finish.

---

## 6. Troubleshooting & Tips

- **LED does not blink?**
    - Only runs as root/sudo or via systemd service.
    - Use `/sys/class/leds/ACT/*` not `led0` for modern Pi OS/Pi Zero 2W.
- **No `/dev/hidg0`?**
    - Confirm use of data cable and check `/boot/config.txt`/`cmdline.txt`.
- **No typing?**
    - Use a USB data cable, the correct USB port, and check your payload.
- **Numbers/special keys not working?**
    - Update to the latest `run_payload.py` implementation for correct mappings.
- **Script typing too slow/fast?**
    - Adjust `KEY_DELAY`, `COMBO_DELAY`, `ENTER_DELAY` at top of `run_payload.py`.
- **BrokenPipeError?**
    - Only run when Pi is plugged into a host and `/dev/hidg0` exists.

---

## Legal Notice
> For use on devices/networks you own or have explicit permission to test. Never use for unauthorized access.

---

## Credits & Contributing
- [Your Name or Handle]
- Inspired by Hak5, Pi, and infosec/maker communities
- Contributions, issues, and PRs are welcome!
