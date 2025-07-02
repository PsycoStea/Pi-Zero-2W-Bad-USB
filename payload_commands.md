# BadUSB Payload Command Reference

Below are the recognised commands your payload.txt can use with this toolkit.

| Command | Description |
| ------- | ----------- |
| `$_JITTER_ENABLED=TRUE/FALSE` | Enable or disable per keystroke jitter (random delay) |
| `$_JITTER_MAX=<int>` | Set maximum jitter delay (ms) |
| `BACKSPACE` | Press the BACKSPACE key |
| `CAPSLOCK` | Press the CAPSLOCK key |
| `CTRL ALT DEL` | Key combo; combine any modifiers with any key (e.g. CTRL ALT DEL) |
| `DEFINE <#KEY> <substitute>` | Define a keyword that will be replaced in subsequent lines |
| `DEL` | Press the DEL key |
| `DELAY <ms>` | Wait given milliseconds before next command |
| `DELETE` | Press the DELETE key |
| `DOWN` | Press the DOWN key |
| `END` | Press the END key |
| `ENTER` | Press the ENTER key |
| `ESC` | Press the ESC key |
| `ESCAPE` | Press the ESCAPE key |
| `F1` | Press the F1 key |
| `F10` | Press the F10 key |
| `F11` | Press the F11 key |
| `F12` | Press the F12 key |
| `F2` | Press the F2 key |
| `F3` | Press the F3 key |
| `F4` | Press the F4 key |
| `F5` | Press the F5 key |
| `F6` | Press the F6 key |
| `F7` | Press the F7 key |
| `F8` | Press the F8 key |
| `F9` | Press the F9 key |
| `HOME` | Press the HOME key |
| `INSERT` | Press the INSERT key |
| `LEFT` | Press the LEFT key |
| `PAGEDOWN` | Press the PAGEDOWN key |
| `PAGEUP` | Press the PAGEUP key |
| `RANDOM_CHAR <count>` | RANDOM_CHAR <count> Types the specified number of random printable characters (letters, digits, special characters). eg. RANDOM_CHAR 12 (Will type 12 characters, e.g. "N7a%K8xLS@3#") |
| `RANDOM_LETTER <count>` | RANDOM_LETTER <count> Types the specified number of random mixed-case letters (a-z, A-Z). eg. RANDOM_LETTER 8 (Will type 8 letters, upper or lower case, e.g. "jLUtyQaM") |
| `RANDOM_LOWERCASE_LETTER <count>` | Types the specified number of random lowercase letters (a-z). eg. RANDOM_LOWERCASE_LETTER 10 (Will type 10 random lowercase letters, such as "msrcqptvab") |
| `RANDOM_NUMBER <count>` | RANDOM_NUMBER <count> Types the specified number of numeric digits (0-9). eg. RANDOM_NUMBER 6 (Will type 6 random digits, e.g. "370215") |
| `RANDOM_SPECIAL <count>` | RANDOM_SPECIAL <count> Types the specified number of special symbols from !@#$%^&*(). eg. RANDOM_SPECIAL 4 (Will type 4 special symbols, e.g. "^%@&")|
| `RANDOM_UPPERCASE_LETTER <count>` | RANDOM_UPPERCASE_LETTER <count> Types the specified number of random uppercase letters (A-Z). eg. RANDOM_UPPERCASE_LETTER 5 (Will type 5 random uppercase letters, such as "ZCTAS") |
| `REM <text>  # Comment` | Comment line (ignored during execution) |
| `RETURN` | Press the RETURN key |
| `RIGHT` | Press the RIGHT key |
| `SPACE` | Press the SPACE key |
| `STRING <text>` | Type the specified text as keystrokes |
| `STRINGLN <text>` | Type the specified text followed by ENTER |
| `TAB` | Press the TAB key |
| `UP` | Press the UP key |
| `VAR <NAME> <content>` | Define a variable that can be injected in the following commands using ${NAME} |
