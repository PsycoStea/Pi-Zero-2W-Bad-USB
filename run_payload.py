#!/usr/bin/env python3
"""Run a Ducky-Script-style payload as USB HID keystrokes.

This module can also be imported directly for tests by passing a custom
``HIDEngine`` to :func:`run_ducky` (see :class:`MockHIDEngine` in the
tests).
"""

from __future__ import annotations

import ast
import os
import random
import re
import string
import sys
import time
from typing import Dict, List, Optional, Tuple

from keymaps import load_layout

# ============================== CONFIG =====================================
KEY_DELAY = 30                     # ms between keystrokes
COMBO_DELAY = 30                   # ms after a key combo
ENTER_DELAY = 50                   # ms after ENTER / RETURN
POST_PAYLOAD_BLINK_WAIT = 500      # ms before the post-payload LED blink
BLINK_PATTERN = [(50, 50)] * 8     # (on_ms, off_ms) per blink

JITTER_ENABLED_DEFAULT = True
JITTER_MAX_DEFAULT = 5             # ms

HID_DEVICE = "/dev/hidg0"
ACT_LED_PATH = "/sys/class/leds/ACT/brightness"
ACT_LED_TRIGGER = "/sys/class/leds/ACT/trigger"

DEFAULT_LAYOUT = "us"

RANDOM_POOLS = {
    "RANDOM_LOWERCASE_LETTER": string.ascii_lowercase,
    "RANDOM_UPPERCASE_LETTER": string.ascii_uppercase,
    "RANDOM_LETTER": string.ascii_letters,
    "RANDOM_NUMBER": string.digits,
    "RANDOM_SPECIAL": "!@#$%^&*()",
    "RANDOM_CHAR": string.ascii_letters + string.digits + "!@#$%^&*()",
}


# ============================== HID engine =================================
class HIDEngine:
    """Writes HID reports to a character device. Opened with no buffering."""

    def __init__(self, path: str = HID_DEVICE) -> None:
        self.path = path
        self._fh = None

    def open(self) -> None:
        self._fh = open(self.path, "wb", buffering=0)

    def write_report(self, report: bytes) -> None:
        assert self._fh is not None, "HIDEngine.open() must be called first"
        self._fh.write(report)

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


# ============================ Math evaluator ===============================
_ALLOWED_MATH_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Pow,
)


def safe_eval_math(expression: str):
    """Evaluate a numeric expression in a sandboxed way (no names, no calls)."""
    expression = expression.strip()
    if not expression:
        raise ValueError("empty expression")
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_MATH_NODES):
            raise ValueError(f"disallowed expression node: {type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError(f"non-numeric constant: {node.value!r}")
    return eval(compile(tree, "<safe_eval_math>", "eval"))


def parse_number(val):
    try:
        if isinstance(val, (int, float)):
            return val
        val_str = str(val).strip()
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except Exception:
        return val


# ============================ Variable substitution ========================
_VAR_RE = re.compile(r"(\$[A-Za-z0-9_]+)")


def substitute_vars(text: str, variables: Dict[str, object]) -> str:
    def repl(match: "re.Match[str]") -> str:
        name = match.group(1)[1:].upper()
        if name in variables:
            return str(variables[name])
        return match.group(0)
    return _VAR_RE.sub(repl, text)


def substitute_defines(line: str, defines: Dict[str, str]) -> str:
    if not defines:
        return line
    for key in sorted(defines, key=lambda k: -len(k)):
        line = line.replace(key, defines[key])
    return line


# ============================ Condition evaluation =========================
_CONDITION_OP_RE = re.compile(r"(==|!=|>=|<=|>|<)")


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def evaluate_condition(condition_str: str, variables: Dict[str, object]) -> bool:
    """Evaluate ``<lhs> <op> <rhs>`` with original case preserved for strings."""
    substituted = substitute_vars(condition_str, variables)
    match = _CONDITION_OP_RE.search(substituted)
    if not match:
        print(f"[WARN] Invalid IF/WHILE condition: {condition_str.strip()}")
        return False
    op = match.group(1)
    lhs_raw = substituted[: match.start()].strip()
    rhs_raw = substituted[match.end():].strip()

    try:
        lhs_val: object = float(lhs_raw)
        rhs_val: object = float(rhs_raw)
    except ValueError:
        lhs_val = _unquote(lhs_raw)
        rhs_val = _unquote(rhs_raw)

    try:
        return {
            "==": lhs_val == rhs_val,
            "!=": lhs_val != rhs_val,
            ">": lhs_val > rhs_val,
            "<": lhs_val < rhs_val,
            ">=": lhs_val >= rhs_val,
            "<=": lhs_val <= rhs_val,
        }[op]
    except TypeError:
        return False


# ============================ LED helpers ==================================
def _safe_write(path: str, value: str) -> None:
    try:
        with open(path, "w") as fh:
            fh.write(value)
    except OSError:
        pass


def led_setup() -> None:
    _safe_write(ACT_LED_TRIGGER, "none")


def led_on() -> None:
    _safe_write(ACT_LED_PATH, "1")


def led_off() -> None:
    _safe_write(ACT_LED_PATH, "0")


def led_blink(pattern, end_on: bool = True) -> None:
    led_setup()
    for on_ms, off_ms in pattern:
        led_on()
        time.sleep(on_ms / 1000)
        led_off()
        time.sleep(off_ms / 1000)
    if end_on:
        led_on()


# ============================ HID-level operations =========================
def send_hid(engine: HIDEngine, mod: int, key: int, release: bool = True) -> None:
    report = bytes([mod & 0xFF, 0x00, key & 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00])
    engine.write_report(report)
    if release:
        engine.write_report(b"\x00\x00\x00\x00\x00\x00\x00\x00")


def type_string(
    engine: HIDEngine,
    text: str,
    keys: Dict[str, Tuple[int, int]],
    modifiers: Dict[str, int],
    jitter_enabled: bool,
    jitter_max: int,
    held_modifiers: int = 0,
) -> None:
    shift = modifiers["SHIFT"]
    for ch in text:
        if ch in keys:
            code, mod = keys[ch]
        elif ch.isupper() and ch.lower() in keys:
            code, base_mod = keys[ch.lower()]
            mod = base_mod | shift
        else:
            print(f"[WARN] Can't type char: {ch!r}")
            continue
        send_hid(engine, mod | held_modifiers, code)
        wait_ms = KEY_DELAY
        if jitter_enabled and jitter_max > 0:
            wait_ms += random.uniform(0, jitter_max)
        time.sleep(wait_ms / 1000)


def press_combo(
    engine: HIDEngine,
    tokens: List[str],
    keys: Dict[str, Tuple[int, int]],
    modifiers: Dict[str, int],
    held_modifiers: int = 0,
) -> None:
    mod = 0
    final_key = 0
    for tok in tokens:
        u = tok.upper()
        if u in modifiers:
            mod |= modifiers[u]
        elif u in keys:
            final_key = keys[u][0]
    send_hid(engine, mod | held_modifiers, final_key)
    time.sleep(COMBO_DELAY / 1000)


# ============================ Parser =======================================
def _new_state(engine: HIDEngine) -> dict:
    modifiers, keys = load_layout(DEFAULT_LAYOUT)
    return {
        "engine": engine,
        "variables": {},
        "defines": {},
        "jitter_enabled": JITTER_ENABLED_DEFAULT,
        "jitter_max": JITTER_MAX_DEFAULT,
        "held_modifier_byte": 0,
        "modifiers": modifiers,
        "keys": keys,
        "layout": DEFAULT_LAYOUT,
    }


def _switch_layout(state: dict, layout_name: str) -> None:
    try:
        modifiers, keys = load_layout(layout_name)
    except ModuleNotFoundError:
        print(f"[WARN] Unknown LAYOUT: {layout_name}")
        return
    state["modifiers"] = modifiers
    state["keys"] = keys
    state["layout"] = layout_name.lower()


def run_ducky(filename: str, engine: Optional[HIDEngine] = None) -> None:
    with open(filename) as fh:
        lines = [ln.rstrip("\n") for ln in fh]

    own_engine = engine is None
    if own_engine:
        engine = HIDEngine()
        engine.open()
    assert engine is not None
    state = _new_state(engine)

    try:
        process_lines(lines, state)
    except BrokenPipeError:
        print(f"[ERROR] Broken pipe writing to HID device (is the Pi plugged into a host?)")
        sys.exit(1)
    finally:
        if own_engine:
            engine.close()


def _collect_block(lines: List[str], start: int, opener: str, closer: str) -> Tuple[List[str], int]:
    """Return (content_lines, end_pc_at_closer). Raises ValueError if unmatched."""
    nesting = 1
    content: List[str] = []
    pc = start + 1
    while pc < len(lines):
        upper = lines[pc].strip().upper()
        if upper.startswith(opener):
            nesting += 1
        elif upper == closer:
            nesting -= 1
            if nesting == 0:
                return content, pc
        content.append(lines[pc])
        pc += 1
    raise ValueError(f"Unmatched {opener} starting at line {start + 1}")


def process_lines(lines: List[str], state: dict) -> None:
    pc = 0
    while pc < len(lines):
        rawline = lines[pc]
        line_after_defines = substitute_defines(rawline, state["defines"])
        stripped = line_after_defines.strip()
        upper = stripped.upper()

        # --- Block commands -----------------------------------------------
        if upper.startswith("REM_BLOCK"):
            try:
                _, pc = _collect_block(lines, pc, "REM_BLOCK", "END_REM")
            except ValueError as exc:
                print(f"[WARN] {exc}")
                return
            pc += 1
            continue

        if upper.startswith("STRINGLN_BLOCK"):
            try:
                content, pc = _collect_block(lines, pc, "STRINGLN_BLOCK", "END_STRINGLN")
            except ValueError as exc:
                print(f"[WARN] {exc}")
                return
            if content:
                min_indent = min(
                    (len(l) - len(l.lstrip(" ")) for l in content if l.strip()),
                    default=0,
                )
                for line in content:
                    body = line[min_indent:]
                    type_string(
                        state["engine"], body, state["keys"], state["modifiers"],
                        state["jitter_enabled"], state["jitter_max"], state["held_modifier_byte"],
                    )
                    send_hid(state["engine"], state["held_modifier_byte"], state["keys"]["ENTER"][0])
                    time.sleep(ENTER_DELAY / 1000)
            pc += 1
            continue

        if upper.startswith("STRING_BLOCK"):
            try:
                content, pc = _collect_block(lines, pc, "STRING_BLOCK", "END_STRING")
            except ValueError as exc:
                print(f"[WARN] {exc}")
                return
            full = " ".join(l.strip() for l in content)
            type_string(
                state["engine"], full, state["keys"], state["modifiers"],
                state["jitter_enabled"], state["jitter_max"], state["held_modifier_byte"],
            )
            pc += 1
            continue

        # --- IF / ELSE / END_IF -------------------------------------------
        if_match = re.match(r"IF\s+(.*?)(?:\s+THEN)?$", stripped, re.IGNORECASE)
        if if_match and upper.startswith("IF "):
            condition_str = if_match.group(1)
            condition_met = evaluate_condition(condition_str, state["variables"])

            nesting = 1
            else_pc = -1
            end_if_pc = -1
            temp = pc + 1
            while temp < len(lines):
                ln_upper = lines[temp].strip().upper()
                if ln_upper.startswith("IF "):
                    nesting += 1
                elif ln_upper == "END_IF":
                    nesting -= 1
                    if nesting == 0:
                        end_if_pc = temp
                        break
                elif ln_upper == "ELSE" and nesting == 1:
                    else_pc = temp
                temp += 1

            if end_if_pc == -1:
                print(f"[WARN] Unmatched IF at line {pc + 1}")
                return

            body: List[str] = []
            if condition_met:
                start = pc + 1
                end = else_pc if else_pc != -1 else end_if_pc
                body = lines[start:end]
            elif else_pc != -1:
                body = lines[else_pc + 1:end_if_pc]

            if body:
                process_lines(body, state)

            pc = end_if_pc + 1
            continue

        # --- WHILE / END_WHILE --------------------------------------------
        while_match = re.match(r"WHILE\s+(.*)$", stripped, re.IGNORECASE)
        if while_match and upper.startswith("WHILE "):
            condition = while_match.group(1)
            nesting = 1
            body_lines: List[str] = []
            temp = pc + 1
            while temp < len(lines):
                ln_upper = lines[temp].strip().upper()
                if ln_upper.startswith("WHILE "):
                    nesting += 1
                elif ln_upper == "END_WHILE":
                    nesting -= 1
                    if nesting == 0:
                        break
                body_lines.append(lines[temp])
                temp += 1

            if nesting != 0:
                print(f"[WARN] Unmatched WHILE at line {pc + 1}")
                return

            end_while_pc = temp
            guard = 0
            while evaluate_condition(condition, state["variables"]):
                process_lines(body_lines, state)
                guard += 1
                if guard > 100000:
                    print("[WARN] WHILE loop exceeded 100000 iterations; breaking")
                    break

            pc = end_while_pc + 1
            continue

        # --- VAR -----------------------------------------------------------
        if upper.startswith("VAR "):
            match = re.match(
                r"VAR\s+(\$[A-Za-z0-9_]+)\s*([+\-*/]?=)\s*(.*)",
                stripped,
                re.IGNORECASE,
            )
            if match:
                var_name = match.group(1)[1:].upper()
                operator = match.group(2)
                expression = match.group(3)
                try:
                    substituted = substitute_vars(expression, state["variables"])
                    if operator == "=" and re.match(r'^\s*".*"\s*$', substituted):
                        state["variables"][var_name] = substituted.strip().strip('"')
                    else:
                        rhs = safe_eval_math(substituted)
                        if operator == "=":
                            state["variables"][var_name] = parse_number(rhs)
                        else:
                            current = parse_number(state["variables"].get(var_name, 0))
                            rhs = parse_number(rhs)
                            if operator == "+=":
                                state["variables"][var_name] = current + rhs
                            elif operator == "-=":
                                state["variables"][var_name] = current - rhs
                            elif operator == "*=":
                                state["variables"][var_name] = current * rhs
                            elif operator == "/=":
                                state["variables"][var_name] = int(current / rhs) if rhs != 0 else 0
                except Exception as exc:
                    print(f"[WARN] Error processing VAR '{stripped}': {exc}")
            else:
                print(f"[WARN] Malformed VAR command: {stripped}")
            pc += 1
            continue

        # --- DEFINE --------------------------------------------------------
        if upper.startswith("DEFINE "):
            parts = stripped.split(None, 2)
            if len(parts) >= 3:
                state["defines"][parts[1]] = parts[2]
            else:
                print(f"[WARN] Malformed DEFINE: {stripped}")
            pc += 1
            continue

        # --- LAYOUT --------------------------------------------------------
        if upper.startswith("LAYOUT "):
            parts = stripped.split(None, 1)
            if len(parts) == 2:
                _switch_layout(state, parts[1].strip())
            pc += 1
            continue

        # --- Substitute variables for remaining commands -------------------
        substituted = substitute_vars(line_after_defines, state["variables"])
        stripped_sub = substituted.strip()
        upper_sub = stripped_sub.upper()

        if not stripped_sub or upper_sub.startswith("REM"):
            pc += 1
            continue

        if upper_sub.startswith("DELAY"):
            digits = re.findall(r"\d+", stripped_sub)
            if digits:
                time.sleep(int(digits[0]) / 1000)
            else:
                print(f"[WARN] Malformed DELAY: {stripped_sub}")
            pc += 1
            continue

        if upper_sub.startswith("STRINGLN"):
            txt = stripped_sub[len("STRINGLN"):].lstrip()
            type_string(
                state["engine"], txt, state["keys"], state["modifiers"],
                state["jitter_enabled"], state["jitter_max"], state["held_modifier_byte"],
            )
            send_hid(state["engine"], state["held_modifier_byte"], state["keys"]["ENTER"][0])
            time.sleep(ENTER_DELAY / 1000)
            pc += 1
            continue

        if upper_sub.startswith("STRING"):
            txt = stripped_sub[len("STRING"):].lstrip()
            type_string(
                state["engine"], txt, state["keys"], state["modifiers"],
                state["jitter_enabled"], state["jitter_max"], state["held_modifier_byte"],
            )
            pc += 1
            continue

        if upper_sub.startswith("INJECT_MOD"):
            parts = stripped_sub.split(None, 1)
            if len(parts) == 2:
                token = parts[1].strip()
                value: Optional[int] = None
                try:
                    value = int(token, 0)  # supports 0x prefix and decimal
                except ValueError:
                    u = token.upper()
                    if u in state["modifiers"]:
                        value = state["modifiers"][u]
                if value is None:
                    print(f"[WARN] Cannot INJECT_MOD value: {token}")
                else:
                    state["held_modifier_byte"] = value & 0xFF
                    state["engine"].write_report(
                        bytes([state["held_modifier_byte"], 0, 0, 0, 0, 0, 0, 0])
                    )
            else:
                print(f"[WARN] Malformed INJECT_MOD: {stripped_sub}")
            pc += 1
            continue

        if upper_sub.startswith("HOLD "):
            key = stripped_sub.split(None, 1)[1].strip().upper()
            if key in state["modifiers"]:
                state["held_modifier_byte"] |= state["modifiers"][key]
                state["engine"].write_report(
                    bytes([state["held_modifier_byte"], 0, 0, 0, 0, 0, 0, 0])
                )
            elif key in state["keys"]:
                print(f"[WARN] HOLD of non-modifier key is not supported: {key}")
            else:
                print(f"[WARN] Cannot HOLD unknown key: {key}")
            pc += 1
            continue

        if upper_sub.startswith("RELEASE "):
            key = stripped_sub.split(None, 1)[1].strip().upper()
            if key in state["modifiers"]:
                state["held_modifier_byte"] &= ~state["modifiers"][key] & 0xFF
                state["engine"].write_report(
                    bytes([state["held_modifier_byte"], 0, 0, 0, 0, 0, 0, 0])
                )
            elif key in state["keys"]:
                # non-modifier key release: no held-key state to clear
                pass
            else:
                print(f"[WARN] Cannot RELEASE unknown key: {key}")
            pc += 1
            continue

        if upper_sub.startswith("RANDOM_"):
            parts = stripped_sub.split()
            cmd = parts[0].upper()
            if cmd in RANDOM_POOLS:
                length = 10
                if len(parts) > 1 and parts[1].isdigit():
                    length = int(parts[1])
                pool = RANDOM_POOLS[cmd]
                random_string = "".join(random.choice(pool) for _ in range(length))
                type_string(
                    state["engine"], random_string, state["keys"], state["modifiers"],
                    state["jitter_enabled"], state["jitter_max"], state["held_modifier_byte"],
                )
            else:
                print(f"[WARN] Unknown RANDOM command: {cmd}")
            pc += 1
            continue

        # Combo: a line of modifier+key tokens, e.g. "CTRL ALT DEL"
        tokens = stripped_sub.split()
        tokens_upper = [t.upper() for t in tokens]
        if tokens and all(t in state["modifiers"] or t in state["keys"] for t in tokens_upper):
            if len(tokens_upper) > 1:
                press_combo(
                    state["engine"], tokens_upper, state["keys"], state["modifiers"],
                    state["held_modifier_byte"],
                )
                pc += 1
                continue

        if upper_sub in state["keys"]:
            code, mod = state["keys"][upper_sub]
            final_mod = mod | state["held_modifier_byte"]
            send_hid(state["engine"], final_mod, code, release=True)
            if state["held_modifier_byte"]:
                state["engine"].write_report(
                    bytes([state["held_modifier_byte"], 0, 0, 0, 0, 0, 0, 0])
                )
            time.sleep((ENTER_DELAY if upper_sub in ("ENTER", "RETURN") else KEY_DELAY) / 1000)
            pc += 1
            continue

        print(f"[WARN] Unknown command or unsupported syntax: {stripped_sub}")
        pc += 1


# ============================ Entry point ==================================
def main(argv: List[str]) -> int:
    default_path = "/home/pi/pi-badusb/payload.txt"
    path = argv[1] if len(argv) > 1 else default_path
    run_ducky(path)
    time.sleep(POST_PAYLOAD_BLINK_WAIT / 1000)
    led_blink(BLINK_PATTERN, end_on=True)
    return 0


if __name__ == "__main__":
    # Ensure the script can import the keymaps package regardless of CWD.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv))
