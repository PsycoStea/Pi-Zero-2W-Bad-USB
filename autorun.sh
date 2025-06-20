#!/bin/bash
set -e
sleep 5
/home/pi/pi-badusb/gadget_setup.sh
sleep 5
/usr/bin/python3 /home/pi/pi-badusb/monitor_and_run.py
