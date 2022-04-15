import pytest

from tax import calculate_gain


def test_buy_sell_same_rate_no_fee():
    file_in = "test/buy_sell_same_rate_no_fee.csv"
    gain = calculate_gain(file_in)
    assert 0 == gain


def test_buy_sell_higher_rate_no_fee():
    file_in = "test/buy_sell_higher_rate_no_fee.csv"
    gain = calculate_gain(file_in)
    assert 500 == gain


def test_buy_sell_lower_rate_no_fee():
    file_in = "test/buy_sell_lower_rate_no_fee.csv"
    gain = calculate_gain(file_in)
    assert -500 == gain


@pytest.mark.xfail(reason="Return to implement window")
def test_first_quarter_gain_is_nil():
    assert False