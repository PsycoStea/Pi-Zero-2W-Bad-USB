"""Unit tests for the Ducky-style payload parser in run_payload.py."""

from __future__ import annotations

import os
import tempfile
import textwrap

import pytest

import run_payload
from run_payload import (
    HIDEngine,
    evaluate_condition,
    run_ducky,
    safe_eval_math,
)


# Speed: drop inter-keystroke delays so the test suite runs in <1s.
run_payload.KEY_DELAY = 0
run_payload.COMBO_DELAY = 0
run_payload.ENTER_DELAY = 0
run_payload.JITTER_ENABLED_DEFAULT = False


class MockHIDEngine(HIDEngine):
    """In-memory engine: captures every report instead of writing to /dev/hidg0."""

    def __init__(self) -> None:  # noqa: D401
        self.reports: list[bytes] = []

    def open(self) -> None:
        pass

    def write_report(self, report: bytes) -> None:
        self.reports.append(bytes(report))

    def close(self) -> None:
        pass

    # Helpers for tests --------------------------------------------------
    @property
    def key_reports(self) -> list[bytes]:
        """All non-empty (i.e. not key-release) reports."""
        return [r for r in self.reports if r != b"\x00" * 8]


def _run(text: str) -> MockHIDEngine:
    engine = MockHIDEngine()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(textwrap.dedent(text))
        path = fh.name
    try:
        run_ducky(path, engine=engine)
    finally:
        os.unlink(path)
    return engine


# ============================ safe_eval_math ==============================
class TestSafeEvalMath:
    def test_basic(self):
        assert safe_eval_math("2 + 3") == 5
        assert safe_eval_math("10 - 4") == 6
        assert safe_eval_math("3 * 4") == 12
        assert safe_eval_math("10 % 3") == 1

    def test_parens(self):
        assert safe_eval_math("(2 + 3) * 4") == 20

    def test_unary(self):
        assert safe_eval_math("-5") == -5
        assert safe_eval_math("+7") == 7

    def test_float(self):
        assert safe_eval_math("1.5 + 0.5") == 2.0

    def test_rejects_name(self):
        with pytest.raises(ValueError):
            safe_eval_math("__import__('os')")

    def test_rejects_attribute(self):
        with pytest.raises(ValueError):
            safe_eval_math("os.system('ls')")

    def test_rejects_call(self):
        with pytest.raises(ValueError):
            safe_eval_math("abs(-1)")

    def test_rejects_string_constant(self):
        with pytest.raises(ValueError):
            safe_eval_math("'evil'")


# ============================ evaluate_condition ==========================
class TestEvaluateCondition:
    def test_numeric(self):
        assert evaluate_condition("5 > 3", {})
        assert not evaluate_condition("5 < 3", {})
        assert evaluate_condition("5 == 5", {})
        assert evaluate_condition("5 != 3", {})

    def test_with_variables(self):
        assert evaluate_condition("$x > 3", {"X": 5})
        assert not evaluate_condition("$x > 3", {"X": 1})

    def test_string_literals_preserve_case(self):
        # Regression test: previously the condition was uppercased before
        # comparison, breaking case-sensitive string compares.
        assert evaluate_condition('$name == "Hello"', {"NAME": "Hello"})
        assert not evaluate_condition('$name == "Hello"', {"NAME": "hello"})

    def test_string_inequality(self):
        assert evaluate_condition('$x != "foo"', {"X": "bar"})


# ============================ VAR =========================================
class TestVar:
    def test_var_assignment_and_use(self):
        engine = _run("""
            VAR $X=5
            VAR $Y=$X+3
            STRING $Y
        """)
        # "8" — find that the key report for '8' is present (usage 0x25).
        codes = [r[2] for r in engine.key_reports]
        assert 0x25 in codes

    def test_var_compound_assignment(self):
        engine = _run("""
            VAR $X=10
            VAR $X+=5
            STRING $X
        """)
        # "15" -> '1' (0x1e) then '5' (0x22)
        codes = [r[2] for r in engine.key_reports]
        assert 0x1E in codes and 0x22 in codes

    def test_var_string_literal(self):
        engine = _run('''
            VAR $NAME="World"
            STRING $NAME
        ''')
        # 'W','o','r','l','d' — at minimum 'W' (0x1a usage with shift) appears
        codes = [r[2] for r in engine.key_reports]
        assert 0x1A in codes  # 'w' = 0x04 + 22 = 0x1A


# ============================ IF / ELSE ===================================
class TestIfElse:
    def test_if_true_runs_then_branch(self):
        engine = _run("""
            VAR $X=5
            IF $X > 3
              STRING A
            ELSE
              STRING B
            END_IF
        """)
        codes = [r[2] for r in engine.key_reports]
        # 'A' = 0x04
        assert 0x04 in codes
        # 'B' = 0x05 not present
        assert 0x05 not in codes

    def test_if_false_runs_else_branch(self):
        engine = _run("""
            VAR $X=1
            IF $X > 3
              STRING A
            ELSE
              STRING B
            END_IF
        """)
        codes = [r[2] for r in engine.key_reports]
        assert 0x05 in codes  # B
        assert 0x04 not in codes

    def test_string_compare_case_sensitive(self):
        engine = _run('''
            VAR $N="Hello"
            IF $N == "Hello"
              STRING M
            ELSE
              STRING X
            END_IF
        ''')
        codes = [r[2] for r in engine.key_reports]
        # 'M' = 0x10, 'X' = 0x1B
        assert 0x10 in codes
        assert 0x1B not in codes


# ============================ WHILE =======================================
class TestWhile:
    def test_while_counts(self):
        engine = _run("""
            VAR $I=0
            WHILE $I < 3
              STRING X
              VAR $I=$I+1
            END_WHILE
        """)
        codes = [r[2] for r in engine.key_reports]
        # 'X' = 0x1B; should appear 3 times
        assert codes.count(0x1B) == 3

    def test_while_le_terminates(self):
        engine = _run("""
            VAR $I=0
            WHILE $I <= 2
              STRING Y
              VAR $I=$I+1
            END_WHILE
        """)
        codes = [r[2] for r in engine.key_reports]
        # 'Y' = 0x1C; should appear 3 times (0, 1, 2)
        assert codes.count(0x1C) == 3


# ============================ RANDOM_ =====================================
class TestRandom:
    def test_random_letter_count(self):
        engine = _run("RANDOM_LETTER 7\n")
        # 7 key reports (no extra modifiers, just 7 letter presses + 7 releases)
        assert len(engine.key_reports) == 7

    def test_random_number_only_digits(self):
        engine = _run("RANDOM_NUMBER 10\n")
        digit_usage_range = set(range(0x1E, 0x28))  # 1..9,0
        codes = [r[2] for r in engine.key_reports]
        assert len(codes) == 10
        assert all(c in digit_usage_range for c in codes)

    def test_random_bogus_no_keystrokes(self):
        # Regression: previously RANDOM_BOGUS could fall through to the
        # combo matcher. Now it must produce a warning and zero output.
        engine = _run("RANDOM_BOGUS 5\n")
        assert engine.key_reports == []


# ============================ INJECT_MOD ==================================
class TestInjectMod:
    def test_inject_mod_applies_to_next_string(self):
        engine = _run("""
            INJECT_MOD 0x03
            STRING a
        """)
        # Find the 'a' key report (usage 0x04). Modifier byte must include 0x03.
        a_reports = [r for r in engine.key_reports if r[2] == 0x04]
        assert a_reports, "expected an 'a' keypress"
        assert a_reports[0][0] & 0x03 == 0x03

    def test_inject_mod_zero_releases(self):
        engine = _run("""
            INJECT_MOD 0x03
            STRING a
            INJECT_MOD 0x00
            STRING b
        """)
        b_reports = [r for r in engine.key_reports if r[2] == 0x05]
        assert b_reports
        assert b_reports[0][0] == 0  # no modifier on 'b'


# ============================ HOLD / RELEASE ==============================
class TestHoldRelease:
    def test_hold_shift_capitalizes(self):
        engine = _run("""
            HOLD SHIFT
            STRINGLN abc
            RELEASE SHIFT
        """)
        # Each letter report should carry shift (0x02)
        letter_reports = [r for r in engine.key_reports if r[2] in (0x04, 0x05, 0x06)]
        assert letter_reports
        assert all(r[0] & 0x02 for r in letter_reports)


# ============================ LAYOUT ======================================
class TestLayout:
    def test_us_at_uses_shift_2(self):
        engine = _run("STRING @\n")
        # @ on US = 0x1F (the "2" key) with shift
        report = next(r for r in engine.key_reports if r[2] == 0x1F)
        assert report[0] & 0x02

    def test_uk_at_uses_shift_apostrophe(self):
        engine = _run("""
            LAYOUT UK
            STRING @
        """)
        # @ on UK = 0x34 (the "'" key) with shift
        report = next(r for r in engine.key_reports if r[2] == 0x34)
        assert report[0] & 0x02

    def test_uk_double_quote_uses_shift_2(self):
        engine = _run("""
            LAYOUT UK
            STRING "
        """)
        # On UK, " is Shift+2 (0x1F)
        report = next(r for r in engine.key_reports if r[2] == 0x1F)
        assert report[0] & 0x02

    def test_unknown_layout_keeps_default(self):
        engine = _run("""
            LAYOUT klingon
            STRING @
        """)
        # Should keep US layout — @ stays at 0x1F+shift
        assert any(r[2] == 0x1F and r[0] & 0x02 for r in engine.key_reports)


# ============================ STRING_BLOCK ================================
class TestStringBlocks:
    def test_string_block_joins(self):
        engine = _run("""
            STRING_BLOCK
              hello
              world
            END_STRING
        """)
        # 'h' = 0x0B, ' ' = 0x2C, 'w' = 0x1A should all appear
        codes = [r[2] for r in engine.key_reports]
        assert 0x0B in codes and 0x2C in codes and 0x1A in codes

    def test_stringln_block_emits_enter_per_line(self):
        engine = _run("""
            STRINGLN_BLOCK
              line1
              line2
            END_STRINGLN
        """)
        codes = [r[2] for r in engine.key_reports]
        # 'l' = 0x0F appears twice; ENTER = 0x28 appears at least twice
        assert codes.count(0x28) >= 2


# ============================ Combo =======================================
class TestCombo:
    def test_ctrl_alt_del(self):
        engine = _run("CTRL ALT DEL\n")
        report = next(r for r in engine.key_reports if r[2] == 0x4C)
        assert report[0] & 0x01  # CTRL
        assert report[0] & 0x04  # ALT


# ============================ DELAY =======================================
class TestDelay:
    def test_delay_no_crash(self):
        engine = _run("DELAY 1\nSTRING X\n")
        codes = [r[2] for r in engine.key_reports]
        assert 0x1B in codes
