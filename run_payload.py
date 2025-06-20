import time
import re
import sys


# ==============================================
#        CONFIGURATION SECTION AND DOCS
# ==============================================
# ---- KEY TYPING SPEED ----
KEY_DELAY = 0.03        # Delay between individual keys/letters (seconds, e.g. 0.01 = 10ms)
COMBO_DELAY = 0.03      # Delay after combos (CTRL, ALT, GUI, etc.)
ENTER_DELAY = 0.05      # Delay after ENTER (recommended for best reliability)



# -------- LED BLINK PATTERN SETTINGS --------
# Custom delay (seconds) after the payload before blinking begins:

POST_PAYLOAD_BLINK_WAIT = 3.5  # e.g. wait 1 second after script before blinking

# Custom blink pattern: list of (on_time, off_time) pairs in seconds:
# Example: blink quickly 5 times

BLINK_PATTERN = [(0.1, 0.1)]*6

# Example: blink 3 times slow, pause, 3 times fast:
# BLINK_PATTERN = [(0.5, 0.1)]*3 + [(0.1, 0.1)]*3
# --------------------------------------------



# ==============================================
#           MAIN SCRIPT BEGINS HERE
# ==============================================

HID_DEVICE = '/dev/hidg0'
LED_PATH = '/sys/class/leds/led0/brightness'

MODIFIERS = {
    'CTRL': 0x01,
    'SHIFT': 0x02,
    'ALT': 0x04,
    'GUI': 0x08,   # Windows/Command key
    'CONTROL': 0x01,
    'WINDOWS': 0x08,
    'COMMAND': 0x08,
}

KEYS = {
    **{chr(i): (0x04 + i - ord('a'), 0) for i in range(ord('a'), ord('z')+1)},
    **{chr(i): (0x04 + i - ord('A'), MODIFIERS['SHIFT']) for i in range(ord('A'), ord('Z')+1)},
    '1': (0x1E, 0),'2': (0x1F, 0),'3': (0x20, 0),'4': (0x21, 0),'5': (0x22, 0),'6': (0x23, 0),
    '7': (0x24, 0),'8': (0x25, 0),'9': (0x26, 0),'0': (0x27, 0),
    ')': (0x27, MODIFIERS['SHIFT']),'!': (0x1e, MODIFIERS['SHIFT']),'@': (0x1f, MODIFIERS['SHIFT']),
    '#': (0x20, MODIFIERS['SHIFT']), '$': (0x21, MODIFIERS['SHIFT']), '%': (0x22, MODIFIERS['SHIFT']),
    '^': (0x23, MODIFIERS['SHIFT']), '&': (0x24, MODIFIERS['SHIFT']), '*': (0x25, MODIFIERS['SHIFT']),
    '(': (0x26, MODIFIERS['SHIFT']),'-': (0x2d, 0),'_': (0x2d, MODIFIERS['SHIFT']),
    '=': (0x2e, 0),'+': (0x2e, MODIFIERS['SHIFT']),'[': (0x2f, 0),'{' : (0x2f, MODIFIERS['SHIFT']),
    ']': (0x30, 0),'}': (0x30, MODIFIERS['SHIFT']),'\\': (0x31, 0),'|': (0x31, MODIFIERS['SHIFT']),
    ';': (0x33, 0),':': (0x33, MODIFIERS['SHIFT']), "'": (0x34, 0), '"': (0x34, MODIFIERS['SHIFT']),
    '`': (0x35, 0),'~': (0x35, MODIFIERS['SHIFT']),',': (0x36, 0),'<': (0x36, MODIFIERS['SHIFT']),
    '.': (0x37, 0),'>': (0x37, MODIFIERS['SHIFT']), '/': (0x38, 0),'?': (0x38, MODIFIERS['SHIFT']),
    ' ': (0x2c, 0), '\t': (0x2b, 0), '\n': (0x28, 0), '\r': (0x28, 0),
    'ENTER': (0x28, 0),'RETURN': (0x28, 0),'ESC': (0x29, 0),'ESCAPE': (0x29, 0),
    'BACKSPACE': (0x2a, 0),'TAB': (0x2b, 0),'SPACE': (0x2c, 0),'CAPSLOCK': (0x39, 0),
    'F1': (0x3a, 0),'F2': (0x3b, 0),'F3': (0x3c, 0),'F4': (0x3d, 0),'F5': (0x3e, 0),'F6': (0x3f, 0),
    'F7': (0x40, 0),'F8': (0x41, 0),'F9': (0x42, 0),'F10': (0x43, 0),'F11': (0x44, 0),'F12': (0x45, 0),
    'PRINTSCREEN': (0x46, 0),'SCROLLLOCK': (0x47, 0),'PAUSE': (0x48, 0),'INSERT': (0x49, 0),'HOME': (0x4a, 0),
    'PAGEUP': (0x4b, 0),'DELETE': (0x4c, 0),'END': (0x4d, 0),'PAGEDOWN': (0x4e, 0),
    'RIGHT': (0x4f, 0),'LEFT': (0x50, 0),'DOWN': (0x51, 0),'UP': (0x52, 0), 'DEL': (0x4c, 0),
}



# --------------- LED CONTROL FUNCTIONS ----------------

ACT_LED_PATH = '/sys/class/leds/ACT/brightness'
ACT_LED_TRIGGER = '/sys/class/leds/ACT/trigger'

def led_setup():
    """Set ACT LED for manual control ('none' trigger)."""
    try:
        with open(ACT_LED_TRIGGER, 'w') as f:
            f.write('none')
    except Exception:
        pass

def led_on():
    try:
        with open(ACT_LED_PATH, 'w') as led:
            led.write('1')
    except Exception:
        pass

def led_off():
    try:
        with open(ACT_LED_PATH, 'w') as led:
            led.write('0')
    except Exception:
        pass

def led_blink(pattern, end_on=True):
    """
    Blink pattern: list of (on_time, off_time). Always leaves LED ON when finished if end_on=True.
    """
    led_setup()
    for on_time, off_time in pattern:
        led_on()
        time.sleep(on_time)
        led_off()
        time.sleep(off_time)
    if end_on:
        led_on()



# -------------------- PAYLOAD RUNNER ------------------

def send_hid(hid, mod, key):
    report = bytes([mod, 0x00, key, 0x00, 0x00, 0x00, 0x00, 0x00])
    hid.write(report)
    hid.flush()
    hid.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    hid.flush()

def type_string(hid, text):
    for ch in text:
        if ch in KEYS:
            code, mod = KEYS[ch]
        elif ch.isupper() and ch.lower() in KEYS:
            code, mod0 = KEYS[ch.lower()]
            mod = mod0 | MODIFIERS['SHIFT']
        else:
            print(f"[WARN] Can't type char: {ch!r}")
            continue
        send_hid(hid, mod, code)
        time.sleep(KEY_DELAY)

def press_combo(hid, mod_keys):
    mod = 0
    final_key = 0
    for mk in mod_keys:
        u = mk.upper()
        if u in MODIFIERS:
            mod |= MODIFIERS[u]
        elif u in KEYS:
            final_key = KEYS[u][0]
    send_hid(hid, mod, final_key)
    time.sleep(COMBO_DELAY)

def run_ducky(filename):
    try:
        with open(HID_DEVICE, 'wb') as hid, open(filename) as f:
            for rawline in f:
                line = rawline.strip()
                if not line or line.upper().startswith('REM'):
                    continue
                if line.upper().startswith('DELAY'):
                    matches = re.findall(r'\d+', line)
                    if matches:
                        ms = int(matches[0])
                        time.sleep(ms / 1000.0)
                    else:
                        print(f"[WARN] Malformed DELAY command: {line}")
                    continue
                if line.upper().startswith('STRING'):
                    txt = line[6:].lstrip()
                    type_string(hid, txt)
                    continue
                words = line.upper().split()
                if all(w in MODIFIERS or w in KEYS for w in words):
                    press_combo(hid, words)
                    continue
                if line.upper() in KEYS:
                    code, mod = KEYS[line.upper()]
                    send_hid(hid, mod, code)
                    if line.upper() in ("ENTER", "RETURN"):
                        time.sleep(ENTER_DELAY)
                    else:
                        time.sleep(KEY_DELAY)
                    continue
                print(f"[WARN] Unknown command or unsupported syntax: {rawline.strip()}")
            time.sleep(0.05)
    except BrokenPipeError:
        print(f"[ERROR] Broken pipe writing to {HID_DEVICE} (is the Pi plugged into a host?)")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_ducky('/home/pi/pi-badusb/payload.txt')
    time.sleep(POST_PAYLOAD_BLINK_WAIT)
    led_blink(BLINK_PATTERN, end_on=True)
