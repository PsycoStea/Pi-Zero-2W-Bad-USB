"""Keymap registry for the BadUSB payload runner.

Each layout module (e.g. ``keymaps.us``, ``keymaps.uk``) exports:

* ``MODIFIERS`` — name -> modifier-byte bit
* ``KEYS`` — character or named-key -> (usage_id, modifier_byte)

The runner loads a layout via :func:`load_layout`.
"""

from __future__ import annotations

import importlib
from typing import Dict, Tuple


def load_layout(name: str) -> Tuple[Dict[str, int], Dict[str, Tuple[int, int]]]:
    """Return ``(MODIFIERS, KEYS)`` for the named layout, e.g. ``"us"`` or ``"uk"``."""
    module = importlib.import_module(f"keymaps.{name.lower()}")
    return module.MODIFIERS, module.KEYS
