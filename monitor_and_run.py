#!/usr/bin/env python3
"""Listen for USB host attach events and run the configured payload.

Host *attach* is detected reliably via ``/sys/class/udc/<udc>/state ==
'configured'``. Host *detach* cannot be detected on the Pi Zero 2 W — the
hardware does not expose VBUS sense to the SoC's dwc2 OTG block, so
``state`` and the dwc2 OTG control register stay frozen at their
last-enumerated values when the cable is physically removed (verified
empirically on 2026-05-25).

Workaround: after every payload run we *cause* a disconnect by unbinding
the UDC, sleeping a short cool-down so the host sees us go away (and the
operator has time to physically unplug), then rebinding. If the operator
is still plugged in when we rebind, the host re-enumerates immediately —
which would re-fire the payload — so we apply both a per-fire minimum
inter-fire interval and a hard fires-per-minute rate limit to prevent
runaway loops.

All timings are environment-variable configurable.
"""

from __future__ import annotations

import collections
import logging
import os
import subprocess
import sys
import time

HID_DEVICE = "/dev/hidg0"
PAYLOAD_SCRIPT = "/home/pi/pi-badusb/run_payload.py"
RELOAD_GADGET_SCRIPT = "/home/pi/pi-badusb/reload_gadget.sh"
GADGET_DIR = "/sys/kernel/config/usb_gadget/g1"
UDC_SYSFS = "/sys/class/udc"


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logging.getLogger("badusb").warning(
            "Ignoring non-numeric %s=%r; using default %r", name, raw, default
        )
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logging.getLogger("badusb").warning(
            "Ignoring non-numeric %s=%r; using default %r", name, raw, default
        )
        return default


# Tunables — overrideable via the environment (e.g. via systemctl edit badusb).
POST_PAYLOAD_FLUSH_S = _env_float("BADUSB_POST_PAYLOAD_FLUSH_S", 0.5)
REARM_COOLDOWN_S = _env_float("BADUSB_REARM_COOLDOWN_S", 5.0)
MIN_INTER_FIRE_S = _env_float("BADUSB_MIN_INTER_FIRE_S", 10.0)
MAX_FIRES_PER_MINUTE = _env_int("BADUSB_MAX_FIRES_PER_MINUTE", 6)
RATELIMIT_PAUSE_S = _env_float("BADUSB_RATELIMIT_PAUSE_S", 60.0)

CONFIGURED_DEBOUNCE_S = 0.5
POLL_INTERVAL_S = 0.3

log = logging.getLogger("badusb")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )


def find_udc(retries: int = 30, delay: float = 1.0) -> str:
    for _ in range(retries):
        try:
            entries = os.listdir(UDC_SYSFS)
        except FileNotFoundError:
            entries = []
        if entries:
            return entries[0]
        time.sleep(delay)
    raise RuntimeError(f"No UDC found under {UDC_SYSFS}")


def read_udc_state(udc: str) -> str:
    try:
        with open(f"{UDC_SYSFS}/{udc}/state", "r") as fh:
            return fh.read().strip()
    except OSError:
        return "unknown"


def wait_for_configured(udc: str) -> None:
    while read_udc_state(udc) != "configured":
        time.sleep(POLL_INTERVAL_S)


def _write_udc(value: str) -> bool:
    """Write to the gadget's UDC file via the os.write syscall.

    Going through ``open(...).write("")`` does not actually invoke
    ``write(2)`` with zero bytes, so the kernel never observes the
    unbind. We use ``os.write`` directly with at least one byte to
    guarantee the kernel receives the request.
    """
    udc_file = f"{GADGET_DIR}/UDC"
    payload = (value + "\n").encode()
    try:
        fd = os.open(udc_file, os.O_WRONLY)
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
        return True
    except OSError as exc:
        log.warning("UDC write %r failed: %s", value, exc)
        return False


def force_unbind() -> bool:
    """Unbind the gadget from the UDC (equivalent to physical disconnect)."""
    ok = _write_udc("")
    if ok:
        log.info("Gadget unbound from UDC.")
    return ok


def force_rebind(udc: str) -> bool:
    """Bind the gadget back to the UDC controller."""
    ok = _write_udc(udc)
    if ok:
        log.info("Gadget rebound to UDC %s.", udc)
    return ok


def main() -> int:
    configure_logging()
    log.info("BadUSB listener starting")
    log.info(
        "Tunables: post_flush=%.2fs rearm_cooldown=%.2fs min_inter_fire=%.2fs "
        "max_per_min=%d ratelimit_pause=%.2fs",
        POST_PAYLOAD_FLUSH_S,
        REARM_COOLDOWN_S,
        MIN_INTER_FIRE_S,
        MAX_FIRES_PER_MINUTE,
        RATELIMIT_PAUSE_S,
    )

    try:
        udc = find_udc()
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    log.info("Using UDC: %s", udc)

    last_fire_at = 0.0
    fire_history: "collections.deque[float]" = collections.deque(maxlen=MAX_FIRES_PER_MINUTE * 4)

    while True:
        log.info("Waiting for host (UDC state == 'configured')...")
        wait_for_configured(udc)

        # Debounce — ignore micro-flaps during enumeration.
        time.sleep(CONFIGURED_DEBOUNCE_S)
        if read_udc_state(udc) != "configured":
            log.info("Configured transition was transient; re-waiting")
            continue

        now = time.time()

        # Rate-limit: if we've fired too many times in the last minute, pause.
        recent = [t for t in fire_history if now - t < 60.0]
        if len(recent) >= MAX_FIRES_PER_MINUTE:
            log.warning(
                "Rate limit reached (%d fires in last 60s); pausing for %.0fs",
                len(recent),
                RATELIMIT_PAUSE_S,
            )
            force_unbind()
            time.sleep(RATELIMIT_PAUSE_S)
            force_rebind(udc)
            continue

        # Per-fire cooldown: if we just fired, suppress this transition
        # (the operator is most likely still plugged in from before).
        if now - last_fire_at < MIN_INTER_FIRE_S:
            wait_remaining = MIN_INTER_FIRE_S - (now - last_fire_at)
            log.info(
                "Suppressing repeat fire (only %.1fs since last); unbinding and waiting %.1fs",
                now - last_fire_at,
                wait_remaining,
            )
            force_unbind()
            time.sleep(max(wait_remaining, REARM_COOLDOWN_S))
            force_rebind(udc)
            continue

        if not os.path.exists(HID_DEVICE):
            log.warning("Host configured but %s missing; reloading gadget", HID_DEVICE)
            force_unbind()
            time.sleep(REARM_COOLDOWN_S)
            force_rebind(udc)
            continue

        log.info("Host attached. Running payload.")
        result = subprocess.run(["python3", PAYLOAD_SCRIPT])
        last_fire_at = time.time()
        fire_history.append(last_fire_at)
        log.info(
            "Payload finished (exit %s). Forcing unbind so the device leaves the host.",
            result.returncode,
        )

        time.sleep(POST_PAYLOAD_FLUSH_S)
        force_unbind()
        log.info("Cooling down for %.1fs before rebind.", REARM_COOLDOWN_S)
        time.sleep(REARM_COOLDOWN_S)
        force_rebind(udc)


if __name__ == "__main__":
    sys.exit(main())
