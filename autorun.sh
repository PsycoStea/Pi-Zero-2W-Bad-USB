#!/bin/bash
# Legacy entry point. The supported startup path is the systemd unit
# installed by install.sh — see README.md. This script remains so it
# can be invoked manually for ad-hoc launches without the service.

set -euo pipefail
/home/pi/pi-badusb/gadget_setup.sh
exec /usr/bin/python3 /home/pi/pi-badusb/monitor_and_run.py
