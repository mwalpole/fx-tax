import pytest

from tax import get_ledger


def test_buy_sell_equal():
    filepath = "data/test/rate/buy_sell_equal.csv"
    ledger = get_ledger(filepath, "FIFO")
    assert 0 == ledger.taxable_gains()


def test_buy_lo_sell_hi():
    filepath = "data/test/rate/buy_lo_sell_hi.csv"
    ledger = get_ledger(filepath, "FIFO")
    assert 500 == ledger.taxable_gains()


def test_buy_hi_sell_lo():
    filepath = "data/test/rate/buy_hi_sell_lo.csv"
    ledger = get_ledger(filepath, "FIFO")
    assert -500 == ledger.taxable_gains()


@pytest.mark.xfail(reason="Real example only run locally")
def test_buy_sell_2021():
    filepath = "data/real/2021.csv"
    ledger = get_ledger(filepath, "LIFO")
    assert -500 == ledger.taxable_gains()


@pytest.mark.xfail(reason="Return to implement window")
def test_first_quarter_gain_is_nil():
    assert False


@pytest.mark.xfail(reason="Return to implement fees")
def test_gain_ledger_with_fees():
    assert False
