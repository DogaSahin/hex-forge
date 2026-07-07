import random

import pytest

from app.modules.dice import parser
from app.modules.dice.parser import DiceError


class ScriptedRandom(random.Random):
    """Returns preset values in order for deterministic dice tests."""

    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):  # noqa: ARG002
        return self._values.pop(0)


def test_flat_and_dice_total():
    result = parser.evaluate("2d6+3", ScriptedRandom([2, 5]))
    assert result.total == 10
    dice, flat = result.terms
    assert dice.is_dice and dice.kept == [2, 5] and dice.total == 7
    assert not flat.is_dice and flat.flat == 3 and flat.sign == 1


def test_implicit_single_die():
    result = parser.evaluate("d20", ScriptedRandom([13]))
    assert result.total == 13
    assert result.terms[0].kept == [13]


def test_multiple_terms_and_subtraction():
    result = parser.evaluate("2d6+1d8-1", ScriptedRandom([2, 5, 4]))
    assert result.total == 2 + 5 + 4 - 1
    assert result.terms[-1].sign == -1 and result.terms[-1].flat == 1


def test_whitespace_and_case_insensitive():
    result = parser.evaluate("  2D6 + 3 ", ScriptedRandom([2, 5]))
    assert result.total == 10


@pytest.mark.parametrize(
    "expr",
    ["", "   ", "2d6x", "d1", "1d6+", "+", "0d6", "1001d6", "2d20001"],
)
def test_invalid_expressions_raise(expr):
    with pytest.raises(DiceError):
        parser.evaluate(expr, ScriptedRandom([1] * 10))
