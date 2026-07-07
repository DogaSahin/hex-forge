from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

MAX_DICE = 1000
MAX_SIDES = 10000
MAX_EXPLOSIONS = 100  # per original die


class DiceError(ValueError):
    """Raised for any malformed or out-of-bounds dice expression."""


@dataclass
class TermResult:
    source: str
    sign: int
    is_dice: bool
    total: int
    kept: list[int] = field(default_factory=list)
    discarded: list[int] = field(default_factory=list)
    flat: int | None = None


@dataclass
class RollResult:
    expression: str
    total: int
    terms: list[TermResult]


_TERM_SPLIT = re.compile(r"([+-])")
# Modifiers filled in Task 3; the group is allowed here so terms with mods still tokenize.
_DICE_RE = re.compile(
    r"^(?P<count>\d*)d(?P<sides>\d+)" r"(?P<mods>(?:kh\d*|kl\d*|dh\d*|dl\d*|r\d+|adv|dis|!)*)$"
)
_MOD_RE = re.compile(r"kh\d*|kl\d*|dh\d*|dl\d*|r\d+|adv|dis|!")


def tokenize(expression: str) -> list[tuple[int, str]]:
    cleaned = re.sub(r"\s+", "", expression).lower()
    if not cleaned:
        raise DiceError("empty expression")
    if cleaned[0] not in "+-":
        cleaned = "+" + cleaned
    parts = _TERM_SPLIT.split(cleaned)  # e.g. ['', '+', '2d6', '-', '1']
    terms: list[tuple[int, str]] = []
    tokens = iter(parts[1:])
    for sign_tok in tokens:
        term = next(tokens, "")
        if term == "":
            raise DiceError(f"missing term after '{sign_tok}'")
        terms.append((1 if sign_tok == "+" else -1, term))
    return terms


def _mod_value(mod: str, prefix_len: int, default: int = 1) -> int:
    digits = mod[prefix_len:]
    return int(digits) if digits else default


def _eval_dice(term: str, rng: random.Random) -> tuple[list[int], list[int], int]:
    m = _DICE_RE.match(term)
    if not m:
        raise DiceError(f"invalid term: {term!r}")
    count = int(m.group("count")) if m.group("count") else 1
    sides = int(m.group("sides"))
    mods = _MOD_RE.findall(m.group("mods"))

    if sides < 2:
        raise DiceError(f"dice need >= 2 sides: {term!r}")
    if sides > MAX_SIDES:
        raise DiceError(f"too many sides (max {MAX_SIDES}): {term!r}")

    # Modifier application is added in Task 3; Task 2 supports plain NdM only.
    if mods:
        raise DiceError(f"unsupported modifier in {term!r}")

    if count < 1:
        raise DiceError(f"dice count must be >= 1: {term!r}")
    if count > MAX_DICE:
        raise DiceError(f"too many dice (max {MAX_DICE}): {term!r}")

    pool = [rng.randint(1, sides) for _ in range(count)]
    return pool, [], sum(pool)


def evaluate(expression: str, rng: random.Random | None = None) -> RollResult:
    rng = rng or random.Random()
    terms: list[TermResult] = []
    grand = 0
    for sign, text in tokenize(expression):
        if text.isdigit():
            value = int(text)
            terms.append(TermResult(source=text, sign=sign, is_dice=False, total=value, flat=value))
            grand += sign * value
        else:
            kept, discarded, total = _eval_dice(text, rng)
            terms.append(
                TermResult(
                    source=text,
                    sign=sign,
                    is_dice=True,
                    total=total,
                    kept=kept,
                    discarded=discarded,
                )
            )
            grand += sign * total
    return RollResult(expression=expression, total=grand, terms=terms)
