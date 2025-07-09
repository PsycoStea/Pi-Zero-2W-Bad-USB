#!/bin/bash
set -e

# --- Configuration ---
# This is the partition that will be exposed as a USB drive.
PARTITION="/dev/mmcblk0p3"

GADGET_DIR="/sys/kernel/config/usb_gadget/g1"

# --- Full Teardown ---
if [ -d "$GADGET_DIR" ]; then
    echo "Tearing down existing gadget..."
    if [ -f "$GADGET_DIR/UDC" ] && [ ! -z "$(cat $GADGET_DIR/UDC)" ]; then
        echo "" > "$GADGET_DIR/UDC"
    fi
    rm -rf "$GADGET_DIR"
    sleep 1
fi

# --- Clean Setup ---
echo "Setting up composite gadget (HID + Mass Storage)..."
modprobe libcomposite
mkdir -p "$GADGET_DIR"
cd "$GADGET_DIR"

# 1. Set Device Descriptors
echo 0x1d6b > idVendor      # Linux Foundation
echo 0x0104 > idProduct     # Multifunction Composite Gadget
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

# 2. Add String Descriptors
mkdir -p strings/0x409
echo "badusb-03" > strings/0x409/serialnumber
echo "Pi Zero" > strings/0x409/manufacturer
echo "BadUSB + Storage" > strings/0x409/product

# 3. Create Configuration
mkdir -p configs/c.1/strings/0x409
echo "HID + Mass Storage" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# 4. Create HID Keyboard Function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x01\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' > functions/hid.usb0/report_desc

# 5. Create Mass Storage Function
mkdir -p functions/mass_storage.usb0
echo 1 > functions/mass_storage.usb0/stall
echo 0 > functions/mass_storage.usb0/lun.0/cdrom
echo 0 > functions/mass_storage.usb0/lun.0/ro
echo 0 > functions/mass_storage.usb0/lun.0/nofua
echo "$PARTITION" > functions/mass_storage.usb0/lun.0/file

# 6. Associate functions with the configuration
ln -s functions/hid.usb0 configs/c.1/
ln -s functions/mass_storage.usb0 configs/c.1/

# 7. Bind to UDC to activate
UDC_CONTROLLER=$(ls /sys/class/udc | head -n 1)
echo "$UDC_CONTROLLER" > UDC

# 8. Set permissions for user-space script
chmod 666 /dev/hidg0

echo "Composite gadget setup complete."
