from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import cache, partial
import logging
from queue import SimpleQueue
from tabulate import tabulate
from typing import List

from pydantic import validate_arguments

logger = logging.getLogger("audit.transaction")

ACCOUNTING_RULES = {
    "FIFO": partial(sorted, key=lambda t: t.date),
    "LIFO": partial(sorted, key=lambda t: t.date, reverse=True),
    "HIFO": partial(sorted, key=lambda t: t.rate, reverse=True),
}


@cache
def get_sorting_func_from_rule(accounting_rule="FIFO"):
    return ACCOUNTING_RULES[accounting_rule]


@validate_arguments
@dataclass
class Transaction:
    id: int
    date_str: str
    ccy1: str
    amt1: Decimal
    ccy2: str
    rate: Decimal
    fee: Decimal
    basis: Decimal = None
    diff: Decimal = None
    eur_drawdown: Decimal = Decimal(0)
    usd_drawdown: Decimal = Decimal(0)
    gain: Decimal = Decimal(0)

    @property
    def usd_balance(self):
        return self.usd - self.usd_drawdown

    @property
    def eur_balance(self):
        return abs(self.eur) - self.eur_drawdown

    @property
    def amt2(self):
        return Decimal(self.amt1 * self.rate) * -1

    @property
    def date(self):
        return datetime.strptime(self.date_str, f"%Y%m%d").date()

    @property
    def is_basis(self):
        # i.e. USD sale
        return self.ccy1 == "USD" and self.amt1 < 0

    @property
    def is_taxable(self):
        # i.e. EUR sale
        return self.ccy1 == "EUR" and self.amt1 < 0

    @property
    def eur(self):
        return self.amt1 if self.ccy1 == "EUR" else self.amt2

    @property
    def usd(self):
        return self.amt1 if self.ccy1 == "USD" else self.amt2


@dataclass(order=True)
class Ledger:
    # Accommodate loading batches of transactions
    # Order and filter transactions, manage queue per:
    # 1. accounting rules
    # 2. filter parameters, e.g. up to Q1 2021
    accounting_rule: str
    balance: Decimal = Decimal(0.0)
    gains: List[Decimal] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    basis_queue: SimpleQueue = SimpleQueue()  # simple fifo queue

    def add_transactions(self, transactions):
        sort_func = get_sorting_func_from_rule(self.accounting_rule)
        for transaction in sort_func(transactions):
            self._add_transaction(transaction)

    def _add_transaction(self, transaction):
        if transaction.is_basis:
            self.basis_queue.put(transaction)
        self.transactions.append(transaction)

    def taxable_gains(self):
        return sum(g for g in self.gains if abs(g) > 200)

    def ordered_transactions(self, by="date", reverse=False):
        return sorted(self.transactions, key=lambda t: getattr(t, by), reverse=reverse)

    def report(self, end=None):
        # handle simple case of single fx pair
        # then filter to report for each fx pair
        basis = self.basis_queue.get_nowait()
        for t in self.ordered_transactions(by="date"):
            if t.is_taxable:
                lot_gain = 0
                while t.eur_balance > 0 and self.basis_queue.qsize() > 0:
                    if basis is None:
                        logger.debug("No physical exchange to provide cost basis.")
                        break
                    else:
                        if basis.eur_balance == 0:
                            basis = self.basis_queue.get_nowait()
                    
                    covered_balance = min(map(abs, (t.eur_balance, basis.eur_balance)))
                    t.eur_drawdown += covered_balance
                    basis.eur_drawdown += covered_balance
                    t.diff = round(basis.rate - t.rate, 4)
                    t.basis = basis.rate
                    t.gain += covered_balance * (basis.rate - t.rate)
                    
                    logger.debug(f"IN   > {basis.date}: {basis.ccy2} {basis.eur:,.2f} @ {basis.rate}")
                    logger.debug(f"OUT  < {t.date}: {t.ccy1} {covered_balance:,.2f} @ {t.rate}")
                    logger.debug(f"BAL -> {basis.date}: {basis.ccy2} {basis.eur_balance}")
                    logger.debug(f"GAIN = {t.date}: {t.ccy2} {t.gain:,.2f} @ {t.diff}")
                    logger.debug(f"BAL <- {t.date}: {t.ccy1} {t.eur_balance}")

                    # clear residual basis balance
                    if 0 < basis.eur_balance < 1000:
                        logger.debug(f"Clearing residual basis balance of {basis.eur_balance:,.2f}")
                        basis.eur_drawdown = abs(basis.eur)
                else:
                    self.gains.append(t.gain)
                    logger.debug(f"Overall: ${t.gain:,.2f}")
                    logger.debug("-" * 50)

                

    def show(self):
        headers = (
            "id",
            "date",
            "ccy1",
            "amt1",
            "ccy2",
            "amt2",
            "rate",
            "fee",
            "is_taxable",
            "is_basis",
            "basis",
            "diff",
            "gain",
        )
        rows = [
            [
                t.id,
                t.date,
                t.ccy1,
                t.amt1,
                t.ccy2,
                t.amt2,
                t.rate,
                t.fee,
                t.is_taxable,
                t.is_basis,
                t.basis,
                t.diff,
                t.gain,
            ]
            for t in sorted(self.transactions, key=lambda x: x.date)
        ]
        print(tabulate(rows, headers=headers))

    def __repr__(self):
        return f"Ledger({len(self.transactions)} transactions, ${self.taxable_gains():,} taxable gains)"
