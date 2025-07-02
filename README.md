**Raspberry Pi Zero 2 W BadUSB HID Toolkit**

---

**Project Description**  
This project transforms a Raspberry Pi Zero 2 W into a programmable BadUSB/HID attack device for red teaming, penetration testing, and CTFs. The Pi emulates a USB keyboard ("Human Interface Device") and executes automated payloads via user-provided scripts (compatible with Ducky Script-style syntax).

---

**Features**
- Run arbitrary, parameterised payloads as a USB keyboard.
- Auto-detect host (PC) connections and execute payload on connection.
- Fully resets after each attack for reliable re-triggering (WIP.
- LED indicator support.

---

**Hardware/Software Requirements**
- Raspberry Pi Zero 2 W (running Raspberry Pi OS Lite)
- USB OTG cable (micro-USB to USB-A)
- (Optional) Soldered headers for easy access to serial console
- Python 3
- Root (sudo) access

---

**Setup: Pi Zero 2 W as a USB HID Keyboard**

1. **Enable dwc2 and ConfigFS**  
   Edit `/boot/config.txt` and add at the end:
   ```
   dtoverlay=dwc2
   ```
   Edit `/boot/cmdline.txt` and add **after `rootwait`**:
   ```
   modules-load=dwc2,g_ether
   ```

2. **Install Required Packages**  
   ```bash
   sudo apt update
   sudo apt install python3
   ```

3. **Deploy Scripts & Make Executable**  
   Copy all project files into `/home/pi/pi-badusb/`.  
   Make shell scripts executable:
   ```bash
   chmod +x /home/pi/pi-badusb/*.sh
   ```

4. **Configure Startup (Optional)**  
   To autorun at boot, add the following to your `/etc/rc.local` (before `exit 0`):
   ```bash
   /home/pi/pi-badusb/autorun.sh &
   ```

---

**Usage Instructions**

1. **Prepare a Payload:**  
   Edit or create `payload.txt` in `/home/pi/pi-badusb/`. Use Ducky Script-like commands (e.g., `STRING`, `ENTER`, `DELAY`, combos, etc.).

2. **First-Time Gadget Setup:**  
   ```bash
   sudo /home/pi/pi-badusb/gadget_setup.sh
   ```

3. **Start the Listener:**  
   ```bash
   sudo python3 /home/pi/pi-badusb/monitor_and_run.py
   ```

4. **Insert Pi Zero 2 W into Target Machine:**  
   As soon as a host connection is detected, your payload will execute as a keystroke sequence.

5. **For Reuse:**  
   The device automatically resets itself and waits for the next connection.

---

**Legal Notice**
:warning:  
This tool is for educational purposes, penetration testing, and CTFs, **with explicit permission** only.  
**Never use on machines you do not own or have permission to test. Unauthorized access is illegal.**

---

**Credits**
- Inspired by USB Rubber Ducky, Hak5, and USB Gadget research.  
- Project scripts: Psycostea <3
