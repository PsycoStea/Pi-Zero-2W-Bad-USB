#!/bin/bash
set -e

G="/sys/kernel/config/usb_gadget/g1"
if [ -d "$G" ]; then
  if [ -f "$G/UDC" ]; then
    echo "" | sudo tee $G/UDC
    sleep 1
  fi
  sudo rm -rf "$G"
fi


sudo modprobe libcomposite

cd /sys/kernel/config/usb_gadget
sudo mkdir g1
cd g1

echo 0x1d6b | sudo tee idVendor      # Linux Foundation
echo 0x0104 | sudo tee idProduct     # Multifunction Composite Gadget
echo 0x0100 | sudo tee bcdDevice
echo 0x0200 | sudo tee bcdUSB

sudo mkdir -p strings/0x409
echo "fedcba9876543210" | sudo tee strings/0x409/serialnumber
echo "Pi Zero 2W" | sudo tee strings/0x409/manufacturer
echo "BadUSB" | sudo tee strings/0x409/product

sudo mkdir -p configs/c.1/strings/0x409
echo "Default config" | sudo tee configs/c.1/strings/0x409/configuration
echo 120 | sudo tee configs/c.1/MaxPower

sudo mkdir -p functions/hid.usb0
echo 1 | sudo tee functions/hid.usb0/protocol
echo 1 | sudo tee functions/hid.usb0/subclass
echo 8 | sudo tee functions/hid.usb0/report_length

# Standard HID keyboard report descriptor
echo -ne '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x01\x95\x06\x75\x08\x15\x00\x25\x6>

sudo ln -s functions/hid.usb0 configs/c.1/

echo "$(ls /sys/class/udc)" | sudo tee UDC

# Let normal users access
sudo chmod 666 /dev/hidg0
