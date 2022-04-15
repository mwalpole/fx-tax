import csv
import sys

from transaction import Ledger, Transaction


def get_row_data(file_in=None):
    if file_in is None:
        file_in = "sample.csv"
    with open(f"data/{file_in}", "r") as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        rows = csv.reader(f.readlines(), dialect)
    next(rows)  # skip header
    return rows


def assemble_ledger(file_in=None):
    # EUR purchase txs are recorded on ledger
    # Ledger txs are ranked based on rule and balance
    # EUR sales deplete the balance of a prior purchase tx
    # Ledger also records USD proceeds by date
    # Proceeds are aggregated over a window
    row_data = get_row_data(file_in)
    ledger = Ledger(accounting_rule="FIFO")
    transactions = [Transaction(*item) for item in row_data]
    ledger.add_transactions(transactions)
    return ledger


def show_ledger():
    ledger = assemble_ledger()
    ledger.report()
    return ledger.show()


def calculate_gain(file_in=None):
    ledger = assemble_ledger(file_in)
    ledger.report()
    ledger.show()
    return ledger.gains


if __name__ == "__main__":
    sys.exit(show_ledger())
