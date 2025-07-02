import time
import re
import sys
import random
import string

# ================ CONFIG SECTION ================
KEY_DELAY = 30                     # ms (default: 30 ms)
COMBO_DELAY = 30                   # ms
ENTER_DELAY = 50                   # ms
POST_PAYLOAD_BLINK_WAIT = 500      # ms
BLINK_PATTERN = [(50, 50)] * 8   # (ms, ms) per blink

JITTER_ENABLED_DEFAULT = True
JITTER_MAX_DEFAULT = 5  # ms

HID_DEVICE = '/dev/hidg0'
ACT_LED_PATH = '/sys/class/leds/ACT/brightness'
ACT_LED_TRIGGER = '/sys/class/leds/ACT/trigger'

MODIFIERS = {
    'CTRL': 0x01, 'SHIFT': 0x02, 'ALT': 0x04, 'GUI': 0x08,
    'CONTROL': 0x01, 'WINDOWS': 0x08, 'COMMAND': 0x08,
}

KEYS = {
    **{chr(i): (0x04 + i - ord('a'), 0) for i in range(ord('a'), ord('z') + 1)},
    **{chr(i): (0x04 + i - ord('A'), MODIFIERS['SHIFT']) for i in range(ord('A'), ord('Z') + 1)},
    '1': (0x1E, 0), '2': (0x1F, 0), '3': (0x20, 0), '4': (0x21, 0),
    '5': (0x22, 0), '6': (0x23, 0), '7': (0x24, 0), '8': (0x25, 0),
    '9': (0x26, 0), '0': (0x27, 0),
    ')': (0x27, MODIFIERS['SHIFT']), '!': (0x1e, MODIFIERS['SHIFT']),
    '@': (0x1f, MODIFIERS['SHIFT']), '#': (0x20, MODIFIERS['SHIFT']),
    '$': (0x21, MODIFIERS['SHIFT']), '%': (0x22, MODIFIERS['SHIFT']),
    '^': (0x23, MODIFIERS['SHIFT']), '&': (0x24, MODIFIERS['SHIFT']),
    '*': (0x25, MODIFIERS['SHIFT']), '(': (0x26, MODIFIERS['SHIFT']),
    '-': (0x2d, 0), '_': (0x2d, MODIFIERS['SHIFT']),
    '=': (0x2e, 0), '+': (0x2e, MODIFIERS['SHIFT']),
    '[': (0x2f, 0), '{': (0x2f, MODIFIERS['SHIFT']),
    ']': (0x30, 0), '}': (0x30, MODIFIERS['SHIFT']),
    '\\': (0x31, 0), '|': (0x31, MODIFIERS['SHIFT']),
    ';': (0x33, 0), ':': (0x33, MODIFIERS['SHIFT']),
    "'": (0x34, 0), '"': (0x34, MODIFIERS['SHIFT']),
    '`': (0x35, 0), '~': (0x35, MODIFIERS['SHIFT']),
    ',': (0x36, 0), '<': (0x36, MODIFIERS['SHIFT']),
    '.': (0x37, 0), '>': (0x37, MODIFIERS['SHIFT']),
    '/': (0x38, 0), '?': (0x38, MODIFIERS['SHIFT']),
    ' ': (0x2c, 0),
    '\t': (0x2b, 0),
    '\n': (0x28, 0),
    '\r': (0x28, 0),
    'ENTER': (0x28, 0), 'RETURN': (0x28, 0), 'ESC': (0x29, 0), 'ESCAPE': (0x29, 0),
    'BACKSPACE': (0x2a, 0), 'TAB': (0x2b, 0), 'SPACE': (0x2c, 0), 'CAPSLOCK': (0x39, 0),
    'F1': (0x3a, 0), 'F2': (0x3b, 0), 'F3': (0x3c, 0), 'F4': (0x3d, 0),
    'F5': (0x3e, 0), 'F6': (0x3f, 0), 'F7': (0x40, 0), 'F8': (0x41, 0),
    'F9': (0x42, 0), 'F10': (0x43, 0), 'F11': (0x44, 0), 'F12': (0x45, 0),
    'PRINTSCREEN': (0x46, 0), 'SCROLLLOCK': (0x47, 0), 'PAUSE': (0x48, 0),
    'INSERT': (0x49, 0), 'HOME': (0x4a, 0), 'PAGEUP': (0x4b, 0),
    'DELETE': (0x4c, 0), 'END': (0x4d, 0), 'PAGEDOWN': (0x4e, 0),
    'RIGHT': (0x4f, 0), 'LEFT': (0x50, 0), 'DOWN': (0x51, 0), 'UP': (0x52, 0),
    'DEL': (0x4c, 0)
}

RANDOM_POOLS = {
    "RANDOM_LOWERCASE_LETTER": string.ascii_lowercase,
    "RANDOM_UPPERCASE_LETTER": string.ascii_uppercase,
    "RANDOM_LETTER": string.ascii_letters,
    "RANDOM_NUMBER": string.digits,
    "RANDOM_SPECIAL": "!@#$%^&*()",
    "RANDOM_CHAR": string.ascii_letters + string.digits + "!@#$%^&*()"
}

def led_setup():
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
    led_setup()
    for on_time, off_time in pattern:
        led_on()
        time.sleep(on_time / 1000)
        led_off()
        time.sleep(off_time / 1000)
    if end_on:
        led_on()

def send_hid(hid, mod, key):
    report = bytes([mod, 0x00, key, 0x00, 0x00, 0x00, 0x00, 0x00])
    hid.write(report)
    hid.flush()
    hid.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    hid.flush()

def substitute_vars(text, variables):
    return re.sub(r'\${([A-Za-z0-9_]+)}', lambda m: variables.get(m.group(1), m.group(0)), text)

def substitute_defines(line, defines):
    if not defines: return line
    for key in sorted(defines, key=lambda k: -len(k)):
        line = line.replace(key, defines[key])
    return line

def parse_jitter_config(line):
    m_enabled = re.match(r'^\$_JITTER_ENABLED\s*=\s*(TRUE|FALSE)', line, re.IGNORECASE)
    m_max = re.match(r'^\$_JITTER_MAX\s*=\s*(\d+)', line, re.IGNORECASE)
    if m_enabled:
        value = m_enabled.group(1).upper()
        return ('ENABLED', value == 'TRUE')
    elif m_max:
        value = int(m_max.group(1))
        return ('MAX', value)
    return (None, None)

def type_string(hid, text, jitter_enabled, jitter_max):
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
        wait = KEY_DELAY
        if jitter_enabled and jitter_max > 0:
            wait += random.uniform(0, jitter_max)
        time.sleep(wait / 1000)

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
    time.sleep(COMBO_DELAY / 1000)

def handle_random_injection(hid, cmd, count, jitter_enabled, jitter_max):
    pool = RANDOM_POOLS.get(cmd)
    if pool:
        for _ in range(count):
            ch = random.choice(pool)
            if ch in KEYS:
                code, mod = KEYS[ch]
            elif ch.isupper() and ch.lower() in KEYS:
                code, mod0 = KEYS[ch.lower()]
                mod = mod0 | MODIFIERS['SHIFT']
            else:
                print(f"[WARN] No HID for random chr: {ch!r}")
                continue
            send_hid(hid, mod, code)
            wait = KEY_DELAY
            if jitter_enabled and jitter_max > 0:
                wait += random.uniform(0, jitter_max)
            time.sleep(wait / 1000)

def run_ducky(filename):
    variables = {}
    defines = {}
    lines = []
    with open(filename) as f:
        for rawline in f:
            lines.append(rawline.rstrip('\n'))
    # ---- SETUP PHASE ----
    jitter_enabled = JITTER_ENABLED_DEFAULT
    jitter_max = JITTER_MAX_DEFAULT
    first_payload_idx = 0
    for idx, line in enumerate(lines):
        test_line = line.strip()
        if not test_line or test_line.upper().startswith('REM'): continue
        if test_line.upper().startswith('DEFINE '):
            parts = test_line.split(None, 2)
            if len(parts) >= 3 and parts[1].startswith('#'):
                defines[parts[1]] = parts[2]
            continue
        if test_line.upper().startswith('VAR '):
            parts = test_line.split(None, 2)
            if len(parts) >= 3:
                var_name = parts[1]
                var_value = parts[2]
                variables[var_name] = var_value
            continue
        jitter_type, value = parse_jitter_config(test_line)
        if jitter_type == 'ENABLED':
            jitter_enabled = value
            continue
        if jitter_type == 'MAX':
            jitter_max = value
            continue
        first_payload_idx = idx
        break
    # ---- PAYLOAD PHASE ----
    try:
        with open(HID_DEVICE, 'wb') as hid:
            for rawline in lines[first_payload_idx:]:
                line = rawline.strip()
                if not line or line.upper().startswith('REM'):
                    continue
                # Substitute
                line = substitute_defines(line, defines)
                line = substitute_vars(line, variables)
                # DELAY
                if line.upper().startswith('DELAY'):
                    matches = re.findall(r'\d+', line)
                    if matches:
                        ms = int(matches[0])
                        time.sleep(ms / 1000)
                    else:
                        print(f"[WARN] Malformed DELAY command: {rawline.strip()}")
                    continue
                # STRINGLN
                if line.upper().startswith('STRINGLN'):
                    txt = line[8:].lstrip()
                    type_string(hid, txt, jitter_enabled, jitter_max)
                    send_hid(hid, 0, KEYS['ENTER'][0])
                    time.sleep(ENTER_DELAY / 1000)
                    continue
                # STRING
                if line.upper().startswith('STRING'):
                    txt = line[6:].lstrip()
                    type_string(hid, txt, jitter_enabled, jitter_max)
                    continue
                # RANDOM
                random_match = re.match(r'^(RANDOM_[A-Z_]+)\s*=\s*(\d+)$', line)
                random_match_single = re.match(r'^(RANDOM_[A-Z_]+)$', line)
                if random_match:
                    command = random_match.group(1)
                    count = int(random_match.group(2))
                    handle_random_injection(hid, command, count, jitter_enabled, jitter_max)
                    continue
                elif random_match_single:
                    command = random_match_single.group(1)
                    handle_random_injection(hid, command, 1, jitter_enabled, jitter_max)
                    continue
                # COMBO
                words = line.split()
                words_upper = [w.upper() for w in words]
                if all(w in MODIFIERS or w in KEYS for w in words_upper):
                    press_combo(hid, words_upper)
                    continue
                # SOLO KEY (like ENTER)
                if line.upper() in KEYS:
                    code, mod = KEYS[line.upper()]
                    send_hid(hid, mod, code)
                    if line.upper() in ("ENTER", "RETURN"):
                        time.sleep(ENTER_DELAY / 1000)
                    else:
                        time.sleep(KEY_DELAY / 1000)
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
    time.sleep(POST_PAYLOAD_BLINK_WAIT / 1000)
    led_blink(BLINK_PATTERN, end_on=True)
