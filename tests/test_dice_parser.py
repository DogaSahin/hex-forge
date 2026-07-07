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


class AlwaysMax(random.Random):
    def randint(self, a, b):  # noqa: ARG002
        return b


def test_keep_highest():
    result = parser.evaluate("4d6kh3", ScriptedRandom([1, 2, 3, 4]))
    assert result.total == 9  # 4+3+2
    assert result.terms[0].kept == [2, 3, 4]  # kept in roll order; the 1 is dropped
    assert result.terms[0].discarded == [1]


def test_keep_lowest():
    result = parser.evaluate("4d6kl2", ScriptedRandom([1, 2, 3, 4]))
    assert result.total == 3  # 1+2
    assert sorted(result.terms[0].kept) == [1, 2]


def test_drop_lowest_and_highest():
    low = parser.evaluate("4d6dl1", ScriptedRandom([1, 2, 3, 4]))
    assert low.total == 9 and low.terms[0].discarded == [1]
    high = parser.evaluate("2d20dh1", ScriptedRandom([5, 17]))
    assert high.total == 5 and high.terms[0].discarded == [17]


def test_advantage_keeps_higher():
    result = parser.evaluate("1d20adv", ScriptedRandom([7, 15]))
    assert result.total == 15


def test_disadvantage_keeps_lower():
    result = parser.evaluate("1d20dis", ScriptedRandom([7, 15]))
    assert result.total == 7


def test_advantage_on_multi_die_raises():
    with pytest.raises(DiceError):
        parser.evaluate("2d20adv", ScriptedRandom([1, 2]))


def test_reroll_once():
    # pool [1,1,3,4]; the two 1s reroll to 6 and 2
    result = parser.evaluate("4d6r1", ScriptedRandom([1, 1, 3, 4, 6, 2]))
    assert result.total == 15  # 6+2+3+4
    assert result.terms[0].discarded == [1, 1]


def test_explode_adds_dice_on_max():
    # 6 explodes -> extra die 4 (not max) stops
    result = parser.evaluate("3d6!", ScriptedRandom([6, 2, 3, 4]))
    assert result.total == 15
    assert result.terms[0].kept == [6, 2, 3, 4]


def test_explode_is_capped():
    result = parser.evaluate("1d2!", AlwaysMax())
    assert len(result.terms[0].kept) == parser.MAX_EXPLOSIONS + 1


def test_keep_more_than_rolled_raises():
    with pytest.raises(DiceError):
        parser.evaluate("2d6kh5", ScriptedRandom([1, 2]))
