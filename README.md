# Raspberry Pi Zero 2 W BadUSB HID Toolkit

A programmable BadUSB / HID attack platform built on a Raspberry Pi Zero 2 W.
The Pi enumerates as a USB composite device (keyboard plus an optional
read-only mass-storage volume) and executes Ducky-Script-style payloads
against the host it's plugged into. Designed for authorised red-team
engagements, penetration tests, and CTFs.

> ⚠️ **Legal notice.** Use only on systems you own or have explicit
> written permission to test. Unauthorised access is illegal in most
> jurisdictions, and pretending you didn't know won't help.

---

## Table of contents

1. [Features](#features)
2. [How it works](#how-it-works)
3. [Hardware](#hardware)
4. [Install](#install)
5. [Daily operation](#daily-operation)
6. [Writing payloads](#writing-payloads)
7. [Configuration reference](#configuration-reference)
8. [Architecture notes](#architecture-notes)
9. [Tests](#tests)
10. [Troubleshooting](#troubleshooting)
11. [Repository layout](#repository-layout)
12. [Credits](#credits)

---

## Features

- **Programmable keystroke payloads** in a Ducky-Script-compatible dialect.
- **Reliable host-attach detection** via the UDC `configured` state — no
  spurious payload fires at boot.
- **"Reset between attacks"** that actually works on Pi Zero 2 W
  hardware. Unplug, replug, fire again — no power-cycle.
- **Configurable safeguards** against runaway loops if the device is
  left plugged in: per-fire minimum interval and a fires-per-minute
  rate limit, both env-var overrideable.
- **Optional composite mass-storage gadget** backed by a flat image
  file (read-only by default — exposing your live SD card was the old
  hard-to-debug FS-corruption foot-gun).
- **US and UK keyboard layouts** selectable per payload with `LAYOUT`.
- Variables, `IF` / `ELSE`, `WHILE`, `HOLD` / `RELEASE`, `INJECT_MOD`,
  `RANDOM_*` generators, `STRING_BLOCK` / `STRINGLN_BLOCK`, `DEFINE`.
- **systemd integration** with `ExecStop` that tears the gadget down
  cleanly. No leftover configfs state, restart works without rebooting.
- **udev-managed permissions** for `/dev/hidg0` — no world-writable
  device nodes.
- **34-test pytest suite** for the Ducky parser, runnable on any host
  with no Pi attached.
- **ACT LED status indicator** after each payload run.

---

## How it works

```
+----------------+        USB cable        +-------------+
|  Raspberry Pi  | ===================>>>  |  Host PC    |
|  Zero 2 W      |   (Pi emulates HID +    |  (target)   |
|  (this device) |    optional drive)      |             |
+----------------+                         +-------------+
        |
        |  /home/pi/pi-badusb/
        |
        +-- badusb.service ----> monitor_and_run.py
                                   |
                                   |  on `state == configured`:
                                   v
                                 run_payload.py
                                   |
                                   v
                                 /dev/hidg0  (USB HID gadget)
```

1. At boot, the `badusb.service` systemd unit runs `gadget_setup.sh`,
   which uses configfs/`libcomposite` to compose a USB gadget with an
   HID keyboard function and (optionally) a mass-storage LUN backed by
   a flat image file at `/var/badusb/storage.img`.
2. The unit then runs `monitor_and_run.py`. It polls
   `/sys/class/udc/<udc>/state` and waits for `configured` — the
   USB-spec state that means a host has successfully enumerated the
   gadget. (We do **not** use `/dev/hidg0`'s existence as a signal:
   that's true the moment the gadget binds to the UDC at boot,
   regardless of whether anything is plugged in.)
3. When the host attaches, the listener executes `run_payload.py`,
   which parses `payload.txt` and writes HID reports to `/dev/hidg0`.
4. When the payload finishes, the listener **actively unbinds** the
   gadget from the UDC (the Pi Zero 2 W cannot detect physical
   disconnect via software — see [Architecture notes](#architecture-notes)),
   sleeps a cooldown, and rebinds. The device then waits for the next
   `configured` transition.

---

## Hardware

| Component | Note |
|-----------|------|
| Raspberry Pi Zero 2 W | Tested on 2026-05 hardware revision. Older Pi Zero W with the BCM2835 dwc_otg driver also works in principle, but this README assumes 2 W with dwc2. |
| micro-USB to USB-A cable | Or a "USB stick" form-factor adapter that lets the Pi plug straight into a host port. |
| Optional: separate charger | If you want to power the Pi from a non-host source so the listener can boot before being plugged into a target (otherwise the host port supplies the power). |

The Pi Zero 2 W has two micro-USB ports:

- **`PWR IN`** — power only, doesn't expose USB data lines to the dwc2 OTG block.
- **`USB`** — the OTG data port; this is where you plug into the target.

---

## Software

| Requirement | Why |
|-------------|-----|
| Raspberry Pi OS (Debian Bookworm or Trixie, 64-bit Lite recommended) | The install script writes to `/boot/firmware/...` on Bookworm+ and falls back to `/boot/...` on older images. |
| Python 3 | Comes with Pi OS. |
| `mkfs.vfat` | For formatting the mass-storage backing image on first run. Skip if you disable mass storage. |
| Root access for setup | Touches systemd, udev, and `/boot/firmware/config.txt`. |

---

## Install

Clone or copy the repo into the Pi, then run the installer:

```bash
git clone http://your-gitea/admin/Pi-Zero-2W-Bad-USB.git /home/pi/pi-badusb
cd /home/pi/pi-badusb
sudo ./install.sh
sudo reboot
```

After reboot, enable and start the service:

```bash
sudo systemctl enable --now badusb.service
journalctl -u badusb -f
```

`install.sh` is **idempotent** — re-run it whenever you change project
files. It:

- Detects `/boot/firmware` (Bookworm+) vs `/boot` (older).
- Ensures `dtoverlay=dwc2,dr_mode=otg` is active under an `[all]`
  block in `config.txt`. Raspberry Pi Imager defaults put this line
  inside a `[cm5]` filter that doesn't apply on Pi Zero 2 W; the
  installer appends a sentinel-marked override so re-runs don't
  duplicate it.
- Ensures `modules-load=dwc2` is in `cmdline.txt`.
- Warns if `g_ether` is still present in `cmdline.txt` (it steals the
  UDC from `libcomposite` and breaks gadget mode).
- Installs the systemd unit at `/etc/systemd/system/badusb.service`.
- Installs the udev rule at `/etc/udev/rules.d/99-badusb-hidg.rules`
  so `/dev/hidg0` is group-writable by `plugdev`.
- Adds the `pi` user to `plugdev`.
- Creates `/var/badusb/` for the mass-storage backing image.

---

## Daily operation

```bash
# Start / stop / restart
sudo systemctl start badusb
sudo systemctl stop badusb
sudo systemctl restart badusb              # safe to do while plugged in

# Watch live
journalctl -u badusb -f

# Disable autostart on boot
sudo systemctl disable badusb

# Tune timings (creates an override drop-in)
sudo systemctl edit badusb
# (paste an [Service] block with Environment="BADUSB_REARM_COOLDOWN_S=8" etc)
sudo systemctl restart badusb
```

The service depends on `sys-kernel-config.mount` and the presence of a
UDC, so it can't fire payloads before the gadget is actually ready.

**Editing the payload doesn't require a restart** — `payload.txt` is
read fresh on every plug-in.

---

## Writing payloads

`payload.txt` lives in the install directory. The full command
reference is in [`payload_commands.md`](payload_commands.md).

### Minimal example

```text
REM Open Run dialog and type a greeting via Notepad
LAYOUT US
GUI r
DELAY 1500
STRING notepad
ENTER
DELAY 2500
STRINGLN Hello from the Pi Zero 2 W
```

### Variables, conditionals, loops

```text
VAR $USER="alice"
VAR $COUNT=0
WHILE $COUNT < 3
  STRINGLN Hello $USER (iteration $COUNT)
  VAR $COUNT = $COUNT + 1
END_WHILE

IF $USER == "alice"
  STRINGLN matched
ELSE
  STRINGLN missed
END_IF
```

Math expressions in `VAR` go through an `ast`-walker safe evaluator —
no names, no calls, no attribute access, only numeric literals and
`+ - * / // % **`.

### Holding modifiers

```text
HOLD SHIFT
STRINGLN this line is in capitals
RELEASE SHIFT
```

### Sending arbitrary modifier combinations

```text
REM Hold Ctrl+Shift (0x01 + 0x02) and tap A
INJECT_MOD 0x03
STRING a
REM Release all modifiers
INJECT_MOD 0x00
```

### Randomness

```text
RANDOM_LETTER 12      # 12 random mixed-case letters
RANDOM_NUMBER 6       # 6 random digits
RANDOM_SPECIAL 4      # 4 random ASCII symbols
```

### Keyboard layout

```text
LAYOUT UK             # switch to UK ISO mappings for subsequent STRING/STRINGLN
STRING @ " # ~ £ \ |  # types correctly on a UK-locale host
```

Drop another file into `keymaps/` (alongside `us.py` and `uk.py`) and
the `LAYOUT <name>` directive will pick it up via `importlib`.

---

## Configuration reference

### Mass-storage gadget (top of `gadget_setup.sh`)

| Variable | Default | Meaning |
|----------|---------|---------|
| `ENABLE_MASS_STORAGE` | `1` | `0` for an HID-only gadget. |
| `BACKING_FILE` | `/var/badusb/storage.img` | Flat image exposed to the host. |
| `BACKING_SIZE_MB` | `64` | Created on first run if missing. |
| `BACKING_LABEL` | `BADUSB` | FAT volume label. |
| `MASS_STORAGE_RO` | `1` | Read-only by default. |

These can be overridden per-invocation by setting them in the
environment when running `gadget_setup.sh` manually, or globally via
the unit's `Environment=` directives.

### Listener tunables (`monitor_and_run.py`)

| Env var | Default | Meaning |
|---------|---------|---------|
| `BADUSB_POST_PAYLOAD_FLUSH_S` | `0.5` | Sleep after payload before unbinding so HID writes drain. |
| `BADUSB_REARM_COOLDOWN_S` | `5` | How long the gadget stays dark to the host between unbind and rebind. |
| `BADUSB_MIN_INTER_FIRE_S` | `10` | Minimum seconds between two payload fires; under this, the fire is suppressed and the gadget re-unbinds. |
| `BADUSB_MAX_FIRES_PER_MINUTE` | `6` | Hard cap; over this, pause for `BADUSB_RATELIMIT_PAUSE_S`. |
| `BADUSB_RATELIMIT_PAUSE_S` | `60` | Pause duration after rate-limit trigger. |

Override with:

```bash
sudo systemctl edit badusb
# In the editor:
# [Service]
# Environment="BADUSB_REARM_COOLDOWN_S=8"
# Environment="BADUSB_MIN_INTER_FIRE_S=20"
sudo systemctl restart badusb
```

---

## Architecture notes

### Why the listener uses UDC `state`, not `/dev/hidg0`

The previous implementation tested `/dev/hidg0` existence + writability
as the "host attached" signal. That device node is created the moment
the gadget binds to the UDC at boot — long before any host has actually
enumerated it. So payloads fired immediately on power-up regardless of
where the Pi was plugged.

The reliable signal is `/sys/class/udc/<udc>/state`, which reports the
USB-spec device state. Only `configured` means the host has issued
`SetConfiguration(1)` — the device is now eligible to send HID reports.

### Why we force-unbind after each payload

Detecting physical disconnect on the Pi Zero 2 W is **impossible from
software**: the board doesn't wire VBUS sense to the SoC's dwc2 OTG
block. After a physical unplug:

- `/sys/class/udc/<udc>/state` stays at `configured`.
- `current_speed` stays at `high-speed`.
- The dwc2 `GOTGCTL` register stays at `0x000d0000` (BSesVld bit set).
- No udev events fire.

So instead of waiting for a signal that will never come, the listener
*actively causes* the disconnect: after each payload, it writes `""` to
the gadget's `UDC` configfs file (which the kernel interprets as
unbind), sleeps `BADUSB_REARM_COOLDOWN_S`, then writes the UDC name
back to rebind. The next host plug-in produces a clean `configured`
transition that the listener can detect.

If the operator leaves the Pi plugged in after a payload, the rebind
causes the host to re-enumerate the gadget. To prevent a runaway
fire loop, two safeguards kick in:

1. `BADUSB_MIN_INTER_FIRE_S` — if a `configured` transition happens
   within this window of the previous fire, suppress it and unbind
   again. The gadget cycles silently in the background.
2. `BADUSB_MAX_FIRES_PER_MINUTE` — sliding-window hard cap. Over the
   cap, the listener pauses for `BADUSB_RATELIMIT_PAUSE_S` and logs a
   warning.

### Why we never use `rm -rf` on configfs

configfs's kernel-managed attribute files (`bcdUSB`, `idVendor`,
`webusb/*`, `os_desc/*`, …) cannot be removed by `rm(2)` — the kernel
returns `EPERM`. They are released only when their parent directory
is `rmdir`-ed. Both `gadget_setup.sh` and `teardown_gadget.sh` walk
the configfs tree in canonical libcomposite order — `rmdir` only,
never `rm` on attribute files — and the kernel cleans up the rest
automatically.

### Why the Python helpers use `os.write` not `file.write`

Writing an empty string via `open(path, "w").write("")` does **not**
invoke `write(2)` with zero bytes — CPython's TextIOWrapper elides it.
For configfs unbind (which the kernel interprets from a zero-length
post-newline-strip write), we use `os.write(fd, b"\n")` directly so
the syscall is always issued with at least one byte.

---

## Tests

The Ducky parser has a 34-test pytest suite that runs against a
`MockHIDEngine` (an in-memory drop-in for the real HID writer), so it
needs no Pi and no USB hardware.

```bash
cd /home/pi/pi-badusb
python3 -m pytest tests/
```

Coverage includes:

- `safe_eval_math` accepting arithmetic, rejecting names / calls /
  attribute access / string constants.
- `evaluate_condition` for numeric and case-sensitive string compares.
- `VAR` with `=`, `+=`, `-=`, `*=`, `/=`.
- `IF` / `ELSE` / `END_IF` taking the correct branch.
- `WHILE` / `END_WHILE` iteration counts for `<` and `<=`.
- `RANDOM_*` length correctness; `RANDOM_<unknown>` no-op + warning.
- `INJECT_MOD` modifier byte persistence across subsequent keystrokes.
- `HOLD SHIFT` capitalising each character in `STRINGLN abc`.
- `LAYOUT US` vs `LAYOUT UK` producing different reports for `@` and
  `"`; unknown layout falls back to the previous one.
- `STRING_BLOCK` joining lines; `STRINGLN_BLOCK` honouring min-indent.

---

## Troubleshooting

### "Payload never fires when plugged in"

1. `cat /sys/class/udc/*/state` — must reach `configured` when the
   host enumerates. If it stays at `not attached`, the host isn't
   talking: try a different cable (some are charge-only) or a
   different host port.
2. `lsmod | grep dwc2` — must be loaded. If only `dwc_otg` is there,
   `dtoverlay=dwc2,dr_mode=otg` isn't applying; re-run `install.sh`
   and reboot.
3. `journalctl -u badusb -f` while plugging in — should show
   `Host attached. Running payload.` within ~2s of host enumeration.

### "Payload fires in a loop with the LED blinking, even unplugged"

This was a real bug that's now fixed. If it happens, you've reverted
to a pre-`os.write` build. Make sure `monitor_and_run.py` matches the
current main branch (search for `os.write(fd, payload)`).

### "Service won't restart — `Operation not permitted`"

Pre-fix `gadget_setup.sh` used `rm -rf` on configfs. The current
version uses `teardown_gadget()` — if you see those errors, you have
an old copy. Re-deploy from main.

### "Permission denied on `/dev/hidg0`"

The udev rule needs a hot-plug to apply, or `sudo udevadm trigger`
and a re-login so the `pi` user picks up the `plugdev` group.

### "`g_ether` warning during install"

Remove `g_ether` from `cmdline.txt`; it claims the UDC before
`libcomposite` can bind.

### "Host shows a USB drive but it's not the size I expected"

Mass-storage size is set by `BACKING_SIZE_MB` and only takes effect on
first run when the backing image is created. To resize:

```bash
sudo systemctl stop badusb
sudo rm /var/badusb/storage.img
sudo BACKING_SIZE_MB=256 /home/pi/pi-badusb/gadget_setup.sh
sudo systemctl start badusb
```

### "I want to leave the Pi plugged in without it spamming the host"

That's what `BADUSB_MIN_INTER_FIRE_S` and `BADUSB_MAX_FIRES_PER_MINUTE`
are for. Set them higher via `systemctl edit badusb`. With the
defaults, a Pi left plugged in re-fires every ~15s for the first
minute, then pauses for 60s, then resumes.

---

## Repository layout

```
.
├── README.md                   This file
├── LICENSE                     MIT
├── install.sh                  Idempotent installer (firmware config, systemd, udev, plugdev)
├── gadget_setup.sh             Composes the USB gadget via configfs/libcomposite
├── teardown_gadget.sh          Canonical configfs teardown (wired as ExecStop)
├── reload_gadget.sh            Manual UDC unbind/rebind helper
├── autorun.sh                  Legacy manual-launch wrapper (systemd is preferred)
├── monitor_and_run.py          Listener: waits for host attach, runs payload, forces re-arm
├── run_payload.py              Ducky-Script-style interpreter
├── payload.txt                 Your payload — edit freely; re-read on each plug-in
├── payload_commands.md         Full command reference
├── etc/
│   ├── badusb.service          systemd unit
│   └── 99-badusb-hidg.rules    udev rule for /dev/hidg0 ownership
├── keymaps/
│   ├── __init__.py             Dynamic layout loader
│   ├── us.py                   US ANSI (default)
│   └── uk.py                   UK ISO
└── tests/
    ├── __init__.py
    ├── conftest.py             pytest path setup
    └── test_parser.py          34 parser tests against a MockHIDEngine
```

---

## Credits

- Original project scripts and inspiration: **Psycostea**.
- USB gadget research: USB Rubber Ducky, Hak5, `libcomposite` documentation,
  the dwc2 kernel driver.
- 2026-05 correctness pass: rewrote host-attach detection, made mass
  storage safe, fixed several parser bugs, added a keymap abstraction,
  migrated startup to systemd, added the unit-test harness, and
  worked around the Pi Zero 2 W's hardware-level inability to detect
  physical disconnect.

---

## License

MIT — see [`LICENSE`](LICENSE).
