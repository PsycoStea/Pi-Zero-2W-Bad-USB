#!/bin/bash
G="/sys/kernel/config/usb_gadget/g1"
if [ -d "$G" ]; then
  if [ -f "$G/UDC" ]; then
    echo "Unbinding $G/UDC"
    echo "" > $G/UDC
    sleep 1
    udc=$(ls /sys/class/udc | head -n 1)
    echo "Rebinding $udc to $G/UDC"
    echo "$udc" > $G/UDC
    sleep 1
  fi
fi
