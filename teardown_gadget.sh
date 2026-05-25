#!/bin/bash
# Standalone teardown for the BadUSB composite gadget. Used by the systemd
# unit's ExecStop and available for manual cleanup. Defines and calls the
# same teardown_gadget() function used by gadget_setup.sh.
#
# Safe to run repeatedly: returns 0 if there is no gadget to tear down.

set -euo pipefail

GADGET_DIR="/sys/kernel/config/usb_gadget/g1"

teardown_gadget() {
    local g="$1"
    [ -d "$g" ] || return 0

    if [ -f "$g/UDC" ] && [ -n "$(cat "$g/UDC" 2>/dev/null)" ]; then
        echo "" > "$g/UDC" || true
    fi

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

    if [ -d "$g/strings" ]; then
        find "$g/strings" -mindepth 1 -maxdepth 1 -type d -exec rmdir {} + 2>/dev/null || true
    fi

    if [ -d "$g/functions" ]; then
        find "$g/functions" -mindepth 1 -maxdepth 1 -type d -exec rmdir {} + 2>/dev/null || true
    fi

    rmdir "$g" 2>/dev/null || true
}

teardown_gadget "$GADGET_DIR"
