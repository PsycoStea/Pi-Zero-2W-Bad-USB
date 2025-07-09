import time
import re
import sys
import random
import string

def parse_number(val):
    try:
        if isinstance(val, (int, float)):
            return val
        val = str(val).strip()
        if '.' in val:
            return float(val)
        return int(val)
    except Exception:
        return val

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

def send_hid(hid, mod, key, release=True):
    report = bytes([mod, 0x00, key, 0x00, 0x00, 0x00, 0x00, 0x00])
    hid.write(report)
    hid.flush()
    if release:
        hid.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        hid.flush()

def substitute_vars(text, variables):
    # Replace $var in 'text' with variable value from 'variables' dict
    def repl(match):
        varname = match.group(1)[1:].upper()  # Remove $ and uppercase
        val = variables.get(varname, match.group(0))
        return str(val)
    return re.sub(r'(\$[A-Za-z0-9_]+)', repl, text)

def substitute_defines(line, defines):
    if not defines: return line
    for key in sorted(defines, key=lambda k: -len(k)):
        line = line.replace(key, defines[key])
    return line

def evaluate_math_expression(expression, variables):
    # This function now assumes variables have already been substituted.
    # It's for evaluating a string that should be a mathematical expression.
    processed_expr = expression
    if not re.match(r'^[0-9\s()+\-*\/.]*$', processed_expr):
        raise ValueError("Expression contains non-numeric/non-operator characters")
    return eval(processed_expr)

def evaluate_condition(condition_str, variables):
    condition_str = substitute_vars(condition_str, variables)
    print(f"DEBUG: evaluate_condition - after substitution: {condition_str}")
    match = re.match(r'\s*([^\s=<>!]+)\s*(==|!=|>=|<=|>|<)\s*([^\s=<>!]+)\s*$', condition_str)
    if not match:
        print(f"[WARN] Invalid IF/WHILE condition: {condition_str}")
        return False

    lhs, op, rhs = match.groups()

    # Try to convert both sides to float, so math and comparison work for integers and decimals.
    try:
        lhs_val = float(lhs)
        rhs_val = float(rhs)
    except ValueError:
        lhs_val = lhs.strip('"')
        rhs_val = rhs.strip('"')


    print(f"DEBUG: evaluate_condition - lhs_val: {lhs_val} (type: {type(lhs_val)}), rhs_val: {rhs_val} (type: {type(rhs_val)}), op: {op}")

    if op == '==': return lhs_val == rhs_val
    if op == '!=': return lhs_val != rhs_val
    if op == '>':  return lhs_val > rhs_val
    if op == '<':  return lhs_val < rhs_val
    if op == '>=': return lhs_val >= rhs_val
    if op == '<=': return lhs_val <= rhs_val
    return False

def type_string(hid, text, jitter_enabled, jitter_max, held_modifiers=0):
    for ch in text:
        if ch in KEYS:
            code, mod = KEYS[ch]
        elif ch.isupper() and ch.lower() in KEYS:
            code, mod0 = KEYS[ch.lower()]
            mod = mod0 | MODIFIERS['SHIFT']
        else:
            print(f"[WARN] Can\'t type char: {ch!r}")
            continue
        final_mod = mod | held_modifiers
        send_hid(hid, final_mod, code)
        wait = KEY_DELAY
        if jitter_enabled and jitter_max > 0:
            wait += random.uniform(0, jitter_max)
        time.sleep(wait / 1000)

def press_combo(hid, mod_keys, held_modifiers=0):
    mod = 0
    final_key = 0
    for mk in mod_keys:
        u = mk.upper()
        if u in MODIFIERS:
            mod |= MODIFIERS[u]
        elif u in KEYS:
            final_key = KEYS[u][0]
    final_mod = mod | held_modifiers
    send_hid(hid, final_mod, final_key)
    time.sleep(COMBO_DELAY / 1000)

def run_ducky(filename):
    lines = []
    with open(filename) as f:
        lines = [line.rstrip('\n') for line in f]

    state = {
        'variables': {},
        'defines': {},
        'hid_device': None,
        'jitter_enabled': JITTER_ENABLED_DEFAULT,
        'jitter_max': JITTER_MAX_DEFAULT,
        'held_modifier_byte': 0
    }

    try:
        with open(HID_DEVICE, 'wb') as hid:
            state['hid_device'] = hid
            process_lines(lines, state)
    except BrokenPipeError:
        print(f"[ERROR] Broken pipe writing to {HID_DEVICE} (is the Pi plugged into a host?)")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def process_lines(lines, state):
    pc = 0
    while pc < len(lines):
        rawline = lines[pc]
        
        # --- Pre-substitution for block command detection ---
        line_for_detection = substitute_defines(rawline, state['defines'])
        stripped_line_for_detection = line_for_detection.strip()
        command_upper_for_detection = stripped_line_for_detection.upper()

        # --- Block Commands ---
        if command_upper_for_detection.startswith('REM_BLOCK'):
            nesting = 1
            start_pc = pc
            pc += 1
            while pc < len(lines):
                line_upper = lines[pc].strip().upper()
                if line_upper.startswith('REM_BLOCK'): nesting += 1
                elif line_upper == 'END_REM':
                    nesting -= 1
                    if nesting == 0: break
                pc += 1
            if nesting != 0: print(f"[WARN] Unmatched REM_BLOCK at line {start_pc+1}")
            pc += 1
            continue

        if command_upper_for_detection.startswith('STRING_BLOCK'):
            content = []
            nesting = 1
            start_pc = pc
            pc += 1
            while pc < len(lines):
                line_upper = lines[pc].strip().upper()
                if line_upper.startswith('STRING_BLOCK'): nesting += 1
                elif line_upper == 'END_STRING':
                    nesting -= 1
                    if nesting == 0: break
                content.append(lines[pc])
                pc += 1
            if nesting != 0: print(f"[WARN] Unmatched STRING_BLOCK at line {start_pc+1}")
            
            full_string = ' '.join(l.strip() for l in content)
            type_string(state['hid_device'], full_string, state['jitter_enabled'], state['jitter_max'], state['held_modifier_byte'])
            pc += 1
            continue

        if command_upper_for_detection.startswith('STRINGLN_BLOCK'):
            content = []
            nesting = 1
            start_pc = pc
            pc += 1
            while pc < len(lines):
                line_upper = lines[pc].strip().upper()
                if line_upper.startswith('STRINGLN_BLOCK'): nesting += 1
                elif line_upper == 'END_STRINGLN':
                    nesting -= 1
                    if nesting == 0: break
                content.append(lines[pc])
                pc += 1
            if nesting != 0: print(f"[WARN] Unmatched STRINGLN_BLOCK at line {start_pc+1}")

            if content:
                min_indent = min(len(l) - len(l.lstrip(' ')) for l in content if l.strip())
                for line in content:
                    type_string(state['hid_device'], line[min_indent:], state['jitter_enabled'], state['jitter_max'], state['held_modifier_byte'])
                    send_hid(state['hid_device'], state['held_modifier_byte'], KEYS['ENTER'][0])
                    time.sleep(ENTER_DELAY / 1000)
            pc += 1
            continue

        if_match = re.match(r'IF\s+(.*?)(\s+THEN)?$', command_upper_for_detection, re.IGNORECASE)
        if if_match:
            condition_met = evaluate_condition(if_match.group(1), state['variables'])
            
            nesting_level = 1
            start_line_num = pc + 1
            
            else_pc = -1
            end_if_pc = -1

            temp_pc = pc + 1
            while temp_pc < len(lines):
                line_upper = lines[temp_pc].strip().upper()
                if line_upper.startswith('IF '): nesting_level += 1
                elif line_upper == 'END_IF':
                    nesting_level -= 1
                    if nesting_level == 0:
                        end_if_pc = temp_pc
                        break
                elif line_upper == 'ELSE' and nesting_level == 1:
                    else_pc = temp_pc
                temp_pc += 1

            if end_if_pc == -1:
                print(f"[WARN] Unmatched IF statement at line {start_line_num}")
                pc = len(lines)
                continue

            body_to_process = []
            if condition_met:
                start = pc + 1
                end = else_pc if else_pc != -1 else end_if_pc
                body_to_process = lines[start:end]
            elif else_pc != -1:
                start = else_pc + 1
                end = end_if_pc
                body_to_process = lines[start:end]
            
            if body_to_process:
                process_lines(body_to_process, state)

            pc = end_if_pc + 1
            continue

        while_match = re.match(r'WHILE\s+(.*)', command_upper_for_detection, re.IGNORECASE)
        if while_match:
            condition = while_match.group(1)
            loop_body = []
            nesting_level = 1
            start_loop_pc = pc + 1
            
            temp_pc = pc + 1
            while temp_pc < len(lines):
                line_upper = lines[temp_pc].strip().upper()
                if line_upper.startswith('WHILE '): nesting_level += 1
                elif line_upper == 'END_WHILE':
                    nesting_level -= 1
                    if nesting_level == 0: break
                loop_body.append(lines[temp_pc])
                temp_pc += 1
            
            if nesting_level != 0:
                print(f"[WARN] Unmatched WHILE at line {start_loop_pc}")

            end_while_pc = temp_pc
            
            while evaluate_condition(condition, state['variables']):
                process_lines(loop_body, state)
            
            pc = end_while_pc + 1
            continue

        # --- Single Line Commands ---
        # VAR commands are special, they are not substituted before processing
        is_var_command = stripped_line_for_detection.upper().startswith('VAR ')
        if is_var_command:
            print(f"DEBUG: Processing VAR command: '{stripped_line_for_detection}'")
            match = re.match(r'VAR\s+(\$[A-Za-z0-9_]+)\s*([+\-*\/]?=)\s*(.*)', stripped_line_for_detection, re.IGNORECASE)
            if match:
                var_name, operator, expression = match.groups()
                var_name = var_name[1:].upper()
                try:
                    # Substitute variables in the expression part only
                    substituted_expression = substitute_vars(expression, state['variables'])
                    
                    # If it's a simple assignment of a string literal (after substitution), don't evaluate
                    if operator == '=' and re.match(r'^\s*\".*\"\s*$', substituted_expression):
                        state['variables'][var_name] = substituted_expression.strip().strip('"')
                    else:
                        # Otherwise, evaluate as a math expression
                        rhs_value = evaluate_math_expression(substituted_expression, state['variables'])
                        
                        if operator == '=':
                            state['variables'][var_name] = parse_number(rhs_value)
                        else: # For +=, -=, etc.
                            current_value = parse_number(state['variables'].get(var_name, 0))
                            rhs_value = parse_number(rhs_value)
                            
                            if operator == '+=':
                                new_value = current_value + rhs_value
                            elif operator == '-=':
                                new_value = current_value - rhs_value
                            elif operator == '*=':
                                new_value = current_value * rhs_value
                            elif operator == '/=':
                                new_value = int(current_value / rhs_value) if rhs_value != 0 else 0
                            else: # Should not happen due to regex, but for safety
                                new_value = rhs_value
                            state['variables'][var_name] = new_value
                except Exception as e:
                    print(f"[WARN] Error processing VAR: '{rawline.strip()}'. Error: {e}")
            else:
                print(f"[WARN] Malformed VAR command: '{rawline.strip()}'")
            pc += 1
            continue

        # Apply substitutions for variables and defines for other single line commands
        line = substitute_vars(line_for_detection, state['variables'])
        stripped_line = line.strip()
        command_upper = stripped_line.upper()
        
        if not stripped_line or command_upper.startswith('REM'):
            pc += 1
            continue

        if command_upper.startswith('DELAY'):
            matches = re.findall(r'\d+', stripped_line)
            if matches: time.sleep(int(matches[0]) / 1000)
            else: print(f"[WARN] Malformed DELAY command: {rawline.strip()}")
            pc += 1
            continue
        
        if command_upper.startswith('STRINGLN'):
            txt = stripped_line[len('STRINGLN'):].lstrip()
            txt = substitute_vars(txt, state['variables'])
            type_string(state['hid_device'], txt, state['jitter_enabled'], state['jitter_max'], state['held_modifier_byte'])
            send_hid(state['hid_device'], state['held_modifier_byte'], KEYS['ENTER'][0])
            time.sleep(ENTER_DELAY / 1000)
            pc += 1
            continue

        if command_upper.startswith('STRING'):
            txt = stripped_line[len('STRING'):].lstrip()
            txt = substitute_vars(txt, state['variables'])
            type_string(state['hid_device'], txt, state['jitter_enabled'], state['jitter_max'], state['held_modifier_byte'])
            pc += 1
            continue
        
        if command_upper.startswith('INJECT_MOD '):
            key_to_inject = stripped_line.split(None, 1)[1].upper()
            if key_to_inject in MODIFIERS:
                mod_byte = MODIFIERS[key_to_inject]
                send_hid(state['hid_device'], mod_byte | state['held_modifier_byte'], 0)
            else: print(f"[WARN] Cannot INJECT_MOD non-modifier key: {key_to_inject}")
            pc += 1
            continue

        if command_upper.startswith('HOLD '):
            key_to_hold = stripped_line.split(None, 1)[1].upper()
            if key_to_hold in MODIFIERS:
                state['held_modifier_byte'] |= MODIFIERS[key_to_hold]
                state['hid_device'].write(bytes([state['held_modifier_byte'], 0, 0, 0, 0, 0, 0, 0]))
                state['hid_device'].flush()
            elif key_to_hold in KEYS:
                # For regular keys, we'll combine them with the next keypress
                # No action needed here as the modifier byte is applied to all subsequent keypresses
                pass
            else:
                print(f"[WARN] Cannot HOLD unknown key: {key_to_hold}")
            pc += 1
            continue

        if command_upper.startswith('RELEASE '):
            key_to_release = stripped_line.split(None, 1)[1].upper()
            if key_to_release in MODIFIERS:
                state['held_modifier_byte'] &= ~MODIFIERS[key_to_release]
                state['hid_device'].write(bytes([state['held_modifier_byte'], 0, 0, 0, 0, 0, 0, 0]))
                state['hid_device'].flush()
            elif key_to_release in KEYS:
                # For regular keys, we just acknowledge the release
                pass
            else:
                print(f"[WARN] Cannot RELEASE unknown key: {key_to_release}")
            pc += 1
            continue

        if command_upper.startswith('RANDOM_'):
            parts = stripped_line.split()
            command = parts[0].upper()
            if command in RANDOM_POOLS:
                length = 10  # Default length
                if len(parts) > 1 and parts[1].isdigit():
                    length = int(parts[1])
                
                char_pool = RANDOM_POOLS[command]
                random_string = ''.join(random.choice(char_pool) for _ in range(length))
                
                type_string(state['hid_device'], random_string, state['jitter_enabled'], state['jitter_max'], state['held_modifier_byte'])
                pc += 1
                continue

        words = stripped_line.split()
        words_upper = [w.upper() for w in words]
        if all(w in MODIFIERS or w in KEYS for w in words_upper):
            press_combo(state['hid_device'], words_upper, state['held_modifier_byte'])
            pc += 1
            continue

        if command_upper in KEYS:
            code, mod = KEYS[command_upper]
            final_mod = mod | state['held_modifier_byte']
            send_hid(state['hid_device'], final_mod, code, release=True)
            if state['held_modifier_byte'] != 0:
                state['hid_device'].write(bytes([state['held_modifier_byte'], 0, 0, 0, 0, 0, 0, 0]))
                state['hid_device'].flush()
            if command_upper in ("ENTER", "RETURN"): time.sleep(ENTER_DELAY / 1000)
            else: time.sleep(KEY_DELAY / 1000)
            pc += 1
            continue

        print(f"[WARN] Unknown command or unsupported syntax: {rawline.strip()}")
        pc += 1

if __name__ == "__main__":
    run_ducky('/home/pi/pi-badusb/payload.txt')
    time.sleep(POST_PAYLOAD_BLINK_WAIT / 1000)
    led_blink(BLINK_PATTERN, end_on=True)
