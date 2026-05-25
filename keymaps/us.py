"""US ANSI keyboard layout. HID usage IDs from the USB HID Usage Tables."""

MODIFIERS = {
    "CTRL": 0x01,
    "CONTROL": 0x01,
    "SHIFT": 0x02,
    "ALT": 0x04,
    "GUI": 0x08,
    "WINDOWS": 0x08,
    "COMMAND": 0x08,
}

_SHIFT = MODIFIERS["SHIFT"]

KEYS = {
    # a–z, A–Z
    **{chr(c): (0x04 + c - ord("a"), 0) for c in range(ord("a"), ord("z") + 1)},
    **{chr(c): (0x04 + c - ord("A"), _SHIFT) for c in range(ord("A"), ord("Z") + 1)},

    # Top row digits and their shifted symbols
    "1": (0x1E, 0),
    "2": (0x1F, 0),
    "3": (0x20, 0),
    "4": (0x21, 0),
    "5": (0x22, 0),
    "6": (0x23, 0),
    "7": (0x24, 0),
    "8": (0x25, 0),
    "9": (0x26, 0),
    "0": (0x27, 0),
    "!": (0x1E, _SHIFT),
    "@": (0x1F, _SHIFT),
    "#": (0x20, _SHIFT),
    "$": (0x21, _SHIFT),
    "%": (0x22, _SHIFT),
    "^": (0x23, _SHIFT),
    "&": (0x24, _SHIFT),
    "*": (0x25, _SHIFT),
    "(": (0x26, _SHIFT),
    ")": (0x27, _SHIFT),

    # Punctuation
    "-": (0x2D, 0), "_": (0x2D, _SHIFT),
    "=": (0x2E, 0), "+": (0x2E, _SHIFT),
    "[": (0x2F, 0), "{": (0x2F, _SHIFT),
    "]": (0x30, 0), "}": (0x30, _SHIFT),
    "\\": (0x31, 0), "|": (0x31, _SHIFT),
    ";": (0x33, 0), ":": (0x33, _SHIFT),
    "'": (0x34, 0), '"': (0x34, _SHIFT),
    "`": (0x35, 0), "~": (0x35, _SHIFT),
    ",": (0x36, 0), "<": (0x36, _SHIFT),
    ".": (0x37, 0), ">": (0x37, _SHIFT),
    "/": (0x38, 0), "?": (0x38, _SHIFT),

    # Whitespace
    " ": (0x2C, 0),
    "\t": (0x2B, 0),
    "\n": (0x28, 0),
    "\r": (0x28, 0),

    # Named keys
    "ENTER": (0x28, 0), "RETURN": (0x28, 0),
    "ESC": (0x29, 0), "ESCAPE": (0x29, 0),
    "BACKSPACE": (0x2A, 0), "TAB": (0x2B, 0), "SPACE": (0x2C, 0),
    "CAPSLOCK": (0x39, 0),
    "F1": (0x3A, 0), "F2": (0x3B, 0), "F3": (0x3C, 0), "F4": (0x3D, 0),
    "F5": (0x3E, 0), "F6": (0x3F, 0), "F7": (0x40, 0), "F8": (0x41, 0),
    "F9": (0x42, 0), "F10": (0x43, 0), "F11": (0x44, 0), "F12": (0x45, 0),
    "PRINTSCREEN": (0x46, 0), "SCROLLLOCK": (0x47, 0), "PAUSE": (0x48, 0),
    "INSERT": (0x49, 0), "HOME": (0x4A, 0), "PAGEUP": (0x4B, 0),
    "DELETE": (0x4C, 0), "DEL": (0x4C, 0), "END": (0x4D, 0), "PAGEDOWN": (0x4E, 0),
    "RIGHT": (0x4F, 0), "LEFT": (0x50, 0), "DOWN": (0x51, 0), "UP": (0x52, 0),
}
