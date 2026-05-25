#!/bin/bash
# Compose a USB gadget (HID keyboard, optionally with a mass-storage LUN
# backed by a flat image file) via configfs/libcomposite.
#
# The mass-storage LUN is read-only by default and points at a flat image
# file so that exposing it to a host cannot corrupt the Pi's root
# filesystem. Toggle behaviour at the top of the file.

set -euo pipefail

# --- Configuration -----------------------------------------------------------
ENABLE_MASS_STORAGE=${ENABLE_MASS_STORAGE:-1}     # 0 = HID only
BACKING_FILE=${BACKING_FILE:-/var/badusb/storage.img}
BACKING_SIZE_MB=${BACKING_SIZE_MB:-64}
BACKING_LABEL=${BACKING_LABEL:-BADUSB}
MASS_STORAGE_RO=${MASS_STORAGE_RO:-1}              # 1 = host sees a read-only volume

GADGET_DIR="/sys/kernel/config/usb_gadget/g1"
CONFIGFS_MOUNT="/sys/kernel/config"

# --- Pre-flight --------------------------------------------------------------
if ! mountpoint -q "$CONFIGFS_MOUNT"; then
    echo "Mounting configfs at $CONFIGFS_MOUNT"
    mount -t configfs none "$CONFIGFS_MOUNT"
fi

modprobe libcomposite

if [ ! -d /sys/class/udc ] || [ -z "$(ls -A /sys/class/udc 2>/dev/null)" ]; then
    echo "ERROR: no UDC available under /sys/class/udc — is dwc2 loaded and the Pi in OTG mode?" >&2
    exit 1
fi

# --- Backing file for mass storage ------------------------------------------
ensure_backing_file() {
    if [ ! -f "$BACKING_FILE" ]; then
        echo "Creating mass-storage backing file at $BACKING_FILE (${BACKING_SIZE_MB}M)"
        mkdir -p "$(dirname "$BACKING_FILE")"
        truncate -s "${BACKING_SIZE_MB}M" "$BACKING_FILE"
        if command -v mkfs.vfat >/dev/null 2>&1; then
            mkfs.vfat -n "$BACKING_LABEL" "$BACKING_FILE" >/dev/null
        else
            echo "WARN: mkfs.vfat not available; backing file left unformatted" >&2
        fi
    fi
}

# --- Canonical libcomposite teardown ----------------------------------------
# configfs's auto-managed attribute files (bcdUSB, idVendor, webusb/*, os_desc/*)
# cannot be removed by `rm`; they're only released when their parent directory
# is rmdir-ed. Walk the tree in the right order; never use `rm -rf` here.
teardown_gadget() {
    local g="$1"
    [ -d "$g" ] || return 0

    # Unbind UDC if currently bound
    if [ -f "$g/UDC" ] && [ -n "$(cat "$g/UDC" 2>/dev/null)" ]; then
        echo "" > "$g/UDC" || true
    fi

    # For each config: remove function symlinks, its strings/<lang>, its strings/, then the config dir
    if [ -d "$g/configs" ]; then
        for cfg in "$g"/configs/*/; do
            [ -d "$cfg" ] || continue
            find "$cfg" -mindepth 1 -maxdepth 1 -type l -exec rm {} + 2>/dev/null || true
            if [ -d "$cfg/strings" ]; then
                find "$cfg/strings" -mindepth 1 -maxdepth 1 -type d -exec rmdir {} + 2>/dev/null || true
                rmdir "$cfg/strings" 2>/dev/null || true
            fi
            rmdir "$cfg" 2>/dev/null || true
        done
    fi

    # Top-level strings/<lang>
    if [ -d "$g/strings" ]; then
        find "$g/strings" -mindepth 1 -maxdepth 1 -type d -exec rmdir {} + 2>/dev/null || true
    fi

    # Functions (each is a directory; rmdir-ing it releases all its attributes)
    if [ -d "$g/functions" ]; then
        find "$g/functions" -mindepth 1 -maxdepth 1 -type d -exec rmdir {} + 2>/dev/null || true
    fi

    # Finally remove the gadget root. The kernel cleans up the remaining
    # attribute files (bcdUSB, idVendor, webusb/*, os_desc/*, …) automatically.
    rmdir "$g" 2>/dev/null || true
}

if [ -d "$GADGET_DIR" ]; then
    echo "Tearing down existing gadget..."
    teardown_gadget "$GADGET_DIR"
    sleep 1
fi

# --- Clean setup -------------------------------------------------------------
if [ "$ENABLE_MASS_STORAGE" = "1" ]; then
    echo "Setting up composite gadget (HID + Mass Storage, RO=$MASS_STORAGE_RO)"
    ensure_backing_file
else
    echo "Setting up HID-only gadget"
fi

mkdir -p "$GADGET_DIR"
cd "$GADGET_DIR"

# 1. Device descriptors
echo 0x1d6b > idVendor      # Linux Foundation
echo 0x0104 > idProduct     # Multifunction Composite Gadget
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

# 2. String descriptors
mkdir -p strings/0x409
echo "badusb-04" > strings/0x409/serialnumber
echo "Pi Zero"   > strings/0x409/manufacturer
if [ "$ENABLE_MASS_STORAGE" = "1" ]; then
    echo "BadUSB + Storage" > strings/0x409/product
else
    echo "BadUSB" > strings/0x409/product
fi

# 3. Configuration
mkdir -p configs/c.1/strings/0x409
if [ "$ENABLE_MASS_STORAGE" = "1" ]; then
    echo "HID + Mass Storage" > configs/c.1/strings/0x409/configuration
else
    echo "HID" > configs/c.1/strings/0x409/configuration
fi
echo 250 > configs/c.1/MaxPower

# 4. HID keyboard function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x01\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' > functions/hid.usb0/report_desc

ln -s functions/hid.usb0 configs/c.1/

# 5. Optional mass-storage function
if [ "$ENABLE_MASS_STORAGE" = "1" ]; then
    mkdir -p functions/mass_storage.usb0
    echo 1 > functions/mass_storage.usb0/stall
    echo 0 > functions/mass_storage.usb0/lun.0/cdrom
    echo "$MASS_STORAGE_RO" > functions/mass_storage.usb0/lun.0/ro
    echo 0 > functions/mass_storage.usb0/lun.0/nofua
    echo "$BACKING_FILE" > functions/mass_storage.usb0/lun.0/file
    ln -s functions/mass_storage.usb0 configs/c.1/
fi

# 6. Bind to UDC to activate
UDC_CONTROLLER=$(ls /sys/class/udc | head -n 1)
echo "$UDC_CONTROLLER" > UDC

# HID device permissions are handled by 99-badusb-hidg.rules now.

echo "Gadget setup complete on UDC $UDC_CONTROLLER."
