import pytest

from tax import calculate_gain


def test_buy_sell_same_rate_no_fee():
    filepath = "data/test/buy_sell_same_rate_no_fee.csv"
    gain = calculate_gain(filepath)
    assert 0 == gain


def test_buy_sell_higher_rate_no_fee():
    filepath = "data/test/buy_sell_higher_rate_no_fee.csv"
    gain = calculate_gain(filepath)
    assert 500 == gain


def test_buy_sell_lower_rate_no_fee():
    filepath = "data/test/buy_sell_lower_rate_no_fee.csv"
    gain = calculate_gain(filepath)
    assert -500 == gain


def test_buy_sell_many_no_fee():
    filepath = "data/real/buy_sell_many_no_fee.csv"
    gain = calculate_gain(filepath)
    assert -500 == gain


@pytest.mark.xfail(reason="Return to implement window")
def test_first_quarter_gain_is_nil():
    assert False


@pytest.mark.xfail(reason="Return to implement fees")
def test_gain_report_with_fees():
    assert False
