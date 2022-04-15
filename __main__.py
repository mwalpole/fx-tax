import csv
import sys
import tabulate
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import validate_arguments
from queue import Queue as FifoQueue, LifoQueue, PriorityQueue
from typing import List


RULES = {
    "FIFO": FifoQueue,
    "LIFI": LifoQueue,
    "HIFO": PriorityQueue,
}


def get_row_data():
    with open("data/data.csv", "r") as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        rows = csv.reader(f.readlines(), dialect)
    next(rows)  # skip header
    return rows


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

    @property    
    def amt2(self):
        return float(self.amt1) * float(self.rate)

    @property
    def date(self):
        return datetime.strptime(self.date_str, f"%Y%m%d").date()

    def eur(self):
        return self.amt1 if self.ccy1 == "EUR" else self.amt2

    def usd(self):
        return self.amt1 if self.ccy1 == "USD" else self.amt2


@dataclass(order=True)
class Ledger:
    rule: str
    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, transaction):
        self.transactions.append(transaction)


def assemble_ledger():
    # EUR purchase txs are recorded on ledger
    # Ledger txs are ranked based on rule and balance
    # EUR sales deplete the balance of a prior purchase tx
    # Ledger also records USD proceeds by date
    # Proceeds are aggregated over a window
    txdata = get_row_data()
    ledger = Ledger(rule="FIFO")
    for item in txdata:
        tx = Transaction(*item)
        ledger.add_transaction(tx)
    return ledger


def main():
    ledger = assemble_ledger()
    headers = ["id", "date", "ccy1", "amt1", "ccy2", "amt2", "rate", "fee"]
    rows = [[
        t.id,
        t.date,
        t.ccy1,
        t.amt1,
        t.ccy2,
        t.amt2,
        t.rate,
        t.fee,
    ] for t in ledger.transactions]

    print(tabulate.tabulate(rows, headers=headers))


if __name__ == "__main__":
    sys.exit(main())
