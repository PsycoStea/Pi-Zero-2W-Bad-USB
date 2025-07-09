# BadPi Payload Command Reference

Below are the recognized commands your payload.txt can use with this toolkit.

| Command | Description |
| ------- | ----------- |
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
| `RANDOM_CHAR <count>` | Types the specified number of random printable characters (letters, digits, special). |
| `RANDOM_LETTER <count>` | Types the specified number of random mixed-case letters. |
| `RANDOM_LOWERCASE_LETTER <count>` | Types a random lowercase string. |
| `RANDOM_NUMBER <count>` | Types random numbers. |
| `RANDOM_SPECIAL <count>` | Types random special characters. |
| `RANDOM_UPPERCASE_LETTER <count>` | Types random uppercase letters. |
| `RETURN` | Press the RETURN key |
| `RIGHT` | Press the RIGHT key |
| `SCROLLLOCK` | Press the SCROLLLOCK key |
| `SHIFT` | Press the SHIFT key |
| `SPACE` | Press the SPACE key |
| `TAB` | Press the TAB key |
| `UP` | Press the UP key |
| `WINDOWS` | Press the WINDOWS key |

---

**Advanced Flow & Logic Commands**

| Command | Description |
| ------- | ----------- |
| `VAR <$name>=<value or expression>` | Create or update a variable. Supports math operators: `+`, `-`, `*`, `/`, `%`. (e.g. `VAR $X=$Y+1`) |
| `IF <var> <operator> <value>` | Begin an IF conditional block (operators: `==`, `!=`, `>`, `<`, `>=`, `<=`). |
| `ELSE` | Alternative branch for IF block. |
| `END_IF` | End of IF or ELSE block. |
| `WHILE <var> <operator> <value>` | Begin a WHILE loop (see IF for operators). |
| `END_WHILE` | End a WHILE block. |

**Comment Blocks**

| Command | Description |
| ------- | ----------- |
| `REM` | Begin a single-line comment. |
| `REM_BLOCK` | Begin a multi-line comment. |
| `END_REM` | End a REM_BLOCK. |

**String and Typing Enhancements**

| Command | Description |
| ------- | ----------- |
| `STRINGLN <text>` | Type text, then press ENTER (newline). |
| `STRING_BLOCK` | Begin multi-line string typing (continues until END_STRING). |
| `END_STRING` | Ends STRING_BLOCK. |
| `STRINGLN_BLOCK` | Begin multi-line string typing, typing each line followed by ENTER. |
| `END_STRINGLN` | Ends STRINGLN_BLOCK. |

**Keyboard State and Modifiers**

| Command | Description |
| ------- | ----------- |
| `HOLD <key/mod>` | Hold a key or modifier (e.g. `HOLD SHIFT`). The key remains held until `RELEASE` is used. |
| `RELEASE <key/mod>` | Release a previously-held key or modifier. |
| `INJECT_MOD <modifier_code>` | Injects a raw hexadecimal modifier byte to be combined with subsequent key presses. This is an advanced command. The byte is a combination of one or more modifier keys. You can add the hex values of the modifiers together to create a combination. For example, to hold CTRL and SHIFT, you would use `0x03` (`0x01` for CTRL + `0x02` for SHIFT). The modifier is released by injecting `0x00`. |

---

# Command Examples

## `VAR <name>=<value or expression>`
```
VAR $COUNT=5
VAR $USERNAME="admin"
VAR $SUM=$COUNT+10
VAR $REMAINDER = 10 % 3
```

## `IF` / `ELSE` / `END_IF`
```
VAR $COUNT=5
IF $COUNT > 3
  STRINGLN Count is greater than 3
ELSE
  STRINGLN Count is not greater than 3
END_IF
```

## `WHILE` / `END_WHILE`
```
VAR $I=0
WHILE $I < 3
  STRINGLN Loop iteration $I
  VAR $I = $I + 1
END_WHILE
```

## `HOLD <key/mod>` / `RELEASE <key/mod>`
```
HOLD SHIFT
STRINGLN this text is in capitals
RELEASE SHIFT
```

## `INJECT_MOD <modifier_code>`

Injects a modifier byte using hexadecimal codes. This is useful for complex key combinations.

**Modifier Codes:**
| Modifier | Hex Code |
| -------- | -------- |
| `CTRL`   | `0x01`   |
| `SHIFT`  | `0x02`   |
| `ALT`    | `0x04`   |
| `GUI`    | `0x08`   |

**Example:**
```
REM Hold down CTRL+SHIFT (0x01 + 0x02 = 0x03)
INJECT_MOD 0x03
STRING a
REM This will type 'A' because SHIFT is held, and send it with CTRL

REM Release all modifiers by injecting 0x00
INJECT_MOD 0x00
STRING a
REM This will type 'a'
```

## `DELAY <ms>`
```
DELAY 500
STRINGLN This types out after a 0.5 second pause
```

## `DEFINE <#KEY> <substitute>`
```
DEFINE #EMAIL user@example.com
STRINGLN My email: #EMAIL
```

## `RANDOM_CHAR <count>`
```
RANDOM_CHAR 10
```
Prints 10 random printable chars.

## `RANDOM_LETTER <count>`
```
RANDOM_LETTER 8
```
Prints 8 random mixed-case letters.

---

## Keys

### Modifier Keys
`ALT`, `CTRL`, `CONTROL`, `SHIFT`, `GUI`, `WINDOWS`, `COMMAND`

### Navigation Keys
`LEFT`, `RIGHT`, `UP`, `DOWN`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN`, `INSERT`, `DELETE`, `DEL`, `BACKSPACE`

### Function Keys
`F1` - `F12`

### Utility Keys
`ENTER`, `RETURN`, `TAB`, `ESC`, `ESCAPE`, `SPACE`, `CAPSLOCK`, `SCROLLLOCK`, `PRINTSCREEN`, `PAUSE`
