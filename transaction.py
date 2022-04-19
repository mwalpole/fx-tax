from dataclasses import dataclass, field
from datetime import datetime
import logging
from queue import Queue as FifoQueue, LifoQueue, PriorityQueue, SimpleQueue
from tabulate import tabulate
from typing import Any, List

from pydantic import validate_arguments

logger = logging.getLogger("audit.transaction")

ACCOUNTING_RULES = {
    "FIFO": FifoQueue,
    "LIFI": LifoQueue,
    "HIFO": PriorityQueue,
}


def get_queue_from_rule(accounting_rule="FIFO"):
    return ACCOUNTING_RULES[accounting_rule]


@validate_arguments
@dataclass
class Transaction:
    id: int
    date_str: str
    ccy1: str
    amt1: float
    ccy2: str
    rate: float
    fee: float
    gain: float = 0.0

    @property
    def amt2(self):
        return self.amt1 * self.rate * -1

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
    # Order and filter transactions, manage queues per:
    # 1. accounting rules
    # 2. filter parameters, e.g. up to Q1 2021
    accounting_rule: str
    balance: float = 0.0
    gains: float = 0.0
    transactions: List[Transaction] = field(default_factory=list)
    queue: SimpleQueue = SimpleQueue()  # simple fifo queue

    # @property
    # def queue(self):
    #     queue = get_queue_from_rule(self.accounting_rule)
    #     return queue()

    def add_transactions(self, transactions):
        for transaction in transactions:
            self._add_transaction(transaction)

    def _add_transaction(self, transaction):
        if transaction.is_basis:
            self.queue.put(transaction)
        self.transactions.append(transaction)

    def report(self, end=None):
        logger.debug("Generating report.")
        for transaction in self.transactions:
            if transaction.is_taxable:
                basis = self.queue.get_nowait()
                self.balance += basis.usd
                transaction.gain = (
                    transaction.eur * basis.rate - transaction.eur * transaction.rate
                )
                self.balance -= transaction.usd
                self.gains += transaction.gain

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
                t.gain,
            ]
            for t in self.transactions
        ]
        print(tabulate(rows, headers=headers))
