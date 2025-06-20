
# Ducky Script Command Reference — Pi Zero 2W BadUSB

This project supports a set of Ducky Script-style commands in your payload (`payload.txt`). Use these commands (one per line) for automating keyboard actions. No programming required!

---

## Syntax

- Each command is on its own line.
- Blank lines and lines starting with `REM` (comments) are ignored.
- Commands are case-insensitive (e.g., `STRING`, `String`, or `string` are all valid).

---

## Command List

| Command                | Description |
|------------------------|-------------|
| `REM ...`              | Comment line. Everything after REM is ignored. |
| `DELAY ms`             | Wait/pause for the specified number of milliseconds (e.g., `DELAY 1000` waits 1 second). |
| `STRING text`          | Types the literal text. (e.g., `STRING Hello world!`) |
| `ENTER`                | Presses the Enter/Return key. |
| `TAB`                  | Presses the Tab key. |
| `ESC` or `ESCAPE`      | Presses the Escape key. |
| `BACKSPACE`            | Presses the Backspace key. |
| `SPACE`                | Presses the Space bar. |
| `UP`, `DOWN`, `LEFT`, `RIGHT` | Arrow/navigation keys. |
| `HOME`, `END`          | Home and End keys. |
| `INSERT`               | Insert key. |
| `DELETE` or `DEL`      | Delete key. |
| `PAGEUP`, `PAGEDOWN`   | Page Up or Page Down key. |
| `CAPSLOCK`             | Presses the Caps Lock key. |
| `F1` - `F12`           | Function keys F1 through F12. |
| `PRINTSCREEN`          | Print Screen key. |
| `SCROLLLOCK`           | Scroll Lock key. |
| `PAUSE`                | Pause/Break key. |
| Handy combinations     | Any combo of modifiers (CTRL, ALT, SHIFT, GUI) plus another key (e.g. `CTRL ALT DEL`, `CTRL SHIFT ESC`, `GUI r`, `ALT F4`, `CTRL c`). Case-insensitive, space-separated. |

---

## Modifiers

| Modifier | Effect |
|----------|--------|
| `CTRL` or `CONTROL` | Control key |
| `SHIFT` | Shift key |
| `ALT` | Alt key |
| `GUI` or `WINDOWS` or `COMMAND` | Windows key (or Command on Mac) |

*Combine with action keys for combos (e.g. `CTRL c`)/(e.g. `GUI r`).*

---

## Structure Examples

```
REM Open Notepad, say hello, close Notepad
GUI r
DELAY 300
STRING notepad
ENTER
DELAY 700
STRING Hello from the Pi!
ENTER
ALT F4
```

```
REM Copy selected text
CTRL c
```

---

## Notes

- You can mix and repeat commands. Blank lines are ignored.
- Unknown or unsupported commands will be skipped (and warned in logs).
- Extend the implementation for more keys as needed!

---

**Questions? Feature requests? Contribute on GitHub or open an issue!**
