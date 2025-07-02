#!/bin/bash
set -e
sleep 3
/home/pi/pi-badusb/gadget_setup.sh
sleep 3
/usr/bin/python3 /home/pi/pi-badusb/monitor_and_run.py
