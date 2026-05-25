#!/bin/bash
# Install / refresh the BadUSB toolkit on a Raspberry Pi.
#
# Idempotent: copies the project into /home/pi/pi-badusb (if run from
# elsewhere), installs the systemd unit and the udev rule, ensures dwc2
# is enabled in firmware config, and adds the pi user to the plugdev
# group.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "install.sh must be run as root (use sudo)." >&2
    exit 1
fi

TARGET_DIR="/home/pi/pi-badusb"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect firmware paths (Bookworm/Trixie use /boot/firmware; older /boot)
if [ -d /boot/firmware ]; then
    BOOT_DIR=/boot/firmware
else
    BOOT_DIR=/boot
fi
CONFIG_TXT="$BOOT_DIR/config.txt"
CMDLINE_TXT="$BOOT_DIR/cmdline.txt"

echo "==> Source: $SRC_DIR"
echo "==> Target: $TARGET_DIR"
echo "==> Firmware config: $BOOT_DIR"

# --- 1. Copy project files into TARGET_DIR ----------------------------------
if [ "$SRC_DIR" != "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
    # rsync if present, else fall back to cp -a
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude '.git' --exclude '__pycache__' --exclude 'tests' "$SRC_DIR/" "$TARGET_DIR/"
    else
        cp -a "$SRC_DIR/." "$TARGET_DIR/"
    fi
fi
chown -R pi:pi "$TARGET_DIR"
chmod +x "$TARGET_DIR"/*.sh "$TARGET_DIR"/run_payload.py "$TARGET_DIR"/monitor_and_run.py 2>/dev/null || true

# --- 2. Firmware config (dwc2 overlay + module load) ------------------------
echo "==> Ensuring dtoverlay=dwc2,dr_mode=otg is active for all models in $CONFIG_TXT"
# A bare [all] / [pi02] / unfiltered dtoverlay=dwc2 line applies to the
# Pi Zero 2 W; one inside [cm4]/[cm5]/etc filters does not. Rather than
# parse the filter sections, drop a fresh override block at the end of
# the file — the firmware honours the last assignment.
if ! grep -qE '^# badusb-toolkit dwc2 override' "$CONFIG_TXT"; then
    printf '\n# badusb-toolkit dwc2 override\n[all]\ndtoverlay=dwc2,dr_mode=otg\n' >> "$CONFIG_TXT"
    echo "    Appended override block under [all]"
else
    echo "    Override block already present"
fi

echo "==> Checking $CMDLINE_TXT for modules-load=dwc2"
if ! grep -qE 'modules-load=[^ ]*dwc2' "$CMDLINE_TXT"; then
    echo "    Adding modules-load=dwc2 to cmdline.txt"
    # cmdline.txt is a single line; append space-delimited args
    sed -i 's|$| modules-load=dwc2|' "$CMDLINE_TXT"
fi

# Warn loudly if g_ether is still referenced — it steals the UDC.
if grep -q 'g_ether' "$CMDLINE_TXT"; then
    echo "WARNING: g_ether is referenced in $CMDLINE_TXT — remove it; it conflicts with the composite gadget." >&2
fi

# --- 3. plugdev group + udev rule -------------------------------------------
echo "==> Ensuring pi is in the plugdev group"
getent group plugdev >/dev/null || groupadd plugdev
usermod -a -G plugdev pi

echo "==> Installing udev rule"
install -m 0644 "$SRC_DIR/etc/99-badusb-hidg.rules" /etc/udev/rules.d/99-badusb-hidg.rules
udevadm control --reload
udevadm trigger --subsystem-match=misc || true

# --- 4. systemd unit --------------------------------------------------------
echo "==> Installing systemd unit"
install -m 0644 "$SRC_DIR/etc/badusb.service" /etc/systemd/system/badusb.service
systemctl daemon-reload

# --- 5. Prepare /var/badusb for the mass-storage backing image --------------
mkdir -p /var/badusb
chown pi:pi /var/badusb

echo
echo "Install complete."
echo
echo "Next steps:"
echo "  1. Reboot:    sudo reboot"
echo "  2. Enable:    sudo systemctl enable --now badusb.service"
echo "  3. Tail logs: journalctl -u badusb -f"
echo
echo "Edit your payload at $TARGET_DIR/payload.txt"
