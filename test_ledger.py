import pytest

from tax import get_report


def test_buy_sell_same_rate_no_fee():
    filepath = "data/test/buy_sell_same_rate_no_fee.csv"
    report = get_report(filepath)
    assert 0 == report.gains


def test_buy_sell_higher_rate_no_fee():
    filepath = "data/test/buy_sell_higher_rate_no_fee.csv"
    report = get_report(filepath)
    assert 500 == report.gains


def test_buy_sell_lower_rate_no_fee():
    filepath = "data/test/buy_sell_lower_rate_no_fee.csv"
    report = get_report(filepath)
    assert -500 == report.gains


def test_buy_sell_many_no_fee():
    filepath = "data/real/buy_sell_many_no_fee.csv"
    report = get_report(filepath)
    assert -500 == report.gains


@pytest.mark.xfail(reason="Return to implement window")
def test_first_quarter_gain_is_nil():
    assert False


@pytest.mark.xfail(reason="Return to implement fees")
def test_gain_report_with_fees():
    assert False
