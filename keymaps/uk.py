"""UK ISO keyboard layout.

Inherits the US map and overrides keys that physically differ between
ANSI and ISO layouts (notably the @/" swap, the dedicated #/~ key, the
non-US-backslash key next to left shift, and the £ symbol on Shift+3).
"""

from keymaps.us import KEYS as _US_KEYS, MODIFIERS

_SHIFT = MODIFIERS["SHIFT"]

KEYS = dict(_US_KEYS)

# UK overrides
KEYS['"'] = (0x1F, _SHIFT)      # Shift+2 on UK
KEYS['@'] = (0x34, _SHIFT)      # Shift+' on UK
KEYS["#"] = (0x32, 0)           # dedicated non-US-hash key
KEYS["~"] = (0x32, _SHIFT)      # Shift on non-US-hash key
KEYS["£"] = (0x20, _SHIFT)      # Shift+3 on UK
KEYS["\\"] = (0x64, 0)          # non-US-backslash key (ISO key next to left shift)
KEYS["|"] = (0x64, _SHIFT)
KEYS["¬"] = (0x35, _SHIFT)      # Shift+`
