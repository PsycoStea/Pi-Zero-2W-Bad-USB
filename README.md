Pi Zero 2W BadUSB
A flexible BADUSB/keystroke injection/automation engine using Raspberry Pi Zero 2W, supporting macros, randomization, and realistic typing speeds.

🚀 Features
•Flexible Macros: Use both DEFINE (constants) and VAR (variables) at the top of your payload—order does not matter.
•JITTER for Realism: Keystroke delay uses KEY_DELAY plus a random amount up to JITTER_MAX (never less than KEY_DELAY). JITTER only applies to standard key typing.
•Accurate Timing: All timing values (KEY_DELAY, COMBO_DELAY, ENTER_DELAY, BLINK_PATTERN) are configured in milliseconds for full control.
•Accurate Combos and Enters: COMBO_DELAY and ENTER_DELAY are always precise and are never affected by JITTER for maximum host reliability.
•RANDOM Key Injection: Supports commands like RANDOM_NUMBER, RANDOM_CHAR, etc., with count, for dynamism in payloads.
•Easy Payload Structure: All configuration goes at the top, followed by your main keystroke payload.

⚙️ Configuration
Example configuration block at the top of payload.txt:
DEFINE #GREETING Hello, friend!
VAR user Alice123
$_JITTER_ENABLED = TRUE
$_JITTER_MAX = 5
•KEY_DELAY: Minimum delay between each regular typed key, in milliseconds.
•JITTER_MAX: Maximum added random delay per key (ms). Each keystroke: KEY_DELAY + random(0, JITTER_MAX)
•COMBO_DELAY: Fixed delay after key combos (e.g. CTRL+Something), in ms. Not affected by JITTER.
•ENTER_DELAY: Fixed delay after ENTER/RETURN or STRINGLN, in ms. Not affected by JITTER.
•BLINK_PATTERN: List of (on_ms, off_ms) tuples for ACT LED status at the end.

🖥️ Payload Example
# Setup configuration (order doesn't matter)
DEFINE #WAIT 1000
DEFINE #MSG Welcome to the matrix...
VAR name neo
$_JITTER_ENABLED = TRUE
$_JITTER_MAX = 7

# Payload
DELAY 500
STRING User: ${name}
ENTER
STRING #MSG
ENTER
DELAY #WAIT
STRINGLN Sending some numbers and symbols:
RANDOM_NUMBER = 8
RANDOM_SPECIAL = 4
STRING Script finished!
ENTER

🎲 RANDOM COMMANDS
•RANDOM_LOWERCASE_LETTER [=N]
•RANDOM_UPPERCASE_LETTER [=N]
•RANDOM_LETTER [=N]
•RANDOM_NUMBER [=N]
•RANDOM_SPECIAL [=N]
•RANDOM_CHAR [=N]
Example:
RANDOM_NUMBER = 8
RANDOM_SPECIAL = 6
RANDOM_CHAR    # types one random character

🧩 Setup & Usage
1.Copy your payload to payload.txt.
2.Boot the Pi Zero 2W with your BADUSB image.
3.The script will automatically process setup config, and then type your payload.
4.Watch the ACT LED blink when done, or add your own blink/status patterns.

⚡️ Tips
•Keep KEY_DELAY at a safe minimum for your target OS/language (too fast may cause missed keys).
•Set JITTER_MAX to small values (like 5–10ms) for realism, but not so large as to make input sluggish.
•Place all DEFINE, VAR, and $_JITTER_... lines at the top for clarity. Order doesn’t matter.

🛠️ Contributions & Issues
PRs and issues welcome! See the script comments for extending HID/keyboard mappings or adding new features.
