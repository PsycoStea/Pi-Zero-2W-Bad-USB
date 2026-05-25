#!/bin/bash
# Unbind and rebind the USB gadget so the host re-enumerates it fresh.
set -euo pipefail

GADGET_DIR="/sys/kernel/config/usb_gadget/g1"

if [ ! -d "$GADGET_DIR" ]; then
    echo "Gadget directory $GADGET_DIR not present; nothing to reload." >&2
    exit 0
fi

if [ ! -f "$GADGET_DIR/UDC" ]; then
    echo "No UDC binding file at $GADGET_DIR/UDC." >&2
    exit 0
fi

if [ -z "$(ls -A /sys/class/udc 2>/dev/null)" ]; then
    echo "No UDC available under /sys/class/udc; cannot rebind." >&2
    exit 1
fi

echo "Unbinding gadget"
echo "" > "$GADGET_DIR/UDC"
sleep 1

udc=$(ls /sys/class/udc | head -n 1)
echo "Rebinding gadget to UDC $udc"
echo "$udc" > "$GADGET_DIR/UDC"
sleep 1
