# BadUSB Payload Command Reference

Below are the recognised commands your payload.txt can use with this toolkit.

| Command | Description |
| ------- | ----------- |
| ``$_JITTER_ENABLED=TRUE|FALSE`` | Enable or disable per keystroke jitter (random delay) |
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
| `RANDOM_CHAR` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_CHAR <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_LETTER` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_LETTER <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_LOWERCASE_LETTER` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_LOWERCASE_LETTER <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_NUMBER` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_NUMBER <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_POOLS` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_POOLS <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_SPECIAL` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_SPECIAL <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_UPPERCASE_LETTER` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `RANDOM_UPPERCASE_LETTER <count>` | Type random characters of the specified type; e.g., RANDOM_NUMBER 4 |
| `REM <text>  # Comment` | Comment line (ignored during execution) |
| `RETURN` | Press the RETURN key |
| `RIGHT` | Press the RIGHT key |
| `SPACE` | Press the SPACE key |
| `STRING <text>` | Type the specified text as keystrokes |
| `STRINGLN <text>` | Type the specified text followed by ENTER |
| `TAB` | Press the TAB key |
| `UP` | Press the UP key |
| `VAR <NAME> <content>` | Define a variable that can be injected in the following commands using ${NAME} |
