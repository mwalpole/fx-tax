import argparse
import csv
import logging
import logging.config
import sys
import yaml

from transaction import Ledger, Transaction

logger = logging.getLogger("audit")


def get_row_data(filepath=None):
    with open(filepath, "r") as f:
        logger.debug(f"Reading {filepath}")
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        rows = csv.reader(f.readlines(), dialect)
    next(rows)  # skip header
    return rows


def assemble_ledger(filepath=None):
    # EUR purchase txs are recorded on ledger
    # Ledger txs are ranked based on rule and balance
    # EUR sales deplete the balance of a prior purchase tx
    # Ledger also records USD proceeds by date
    # Proceeds are aggregated over a window
    row_data = get_row_data(filepath)
    ledger = Ledger(accounting_rule="FIFO")
    transactions = [Transaction(*item) for item in row_data]
    ledger.add_transactions(transactions)
    return ledger


def get_report(filepath=None, show=True):
    ledger = assemble_ledger(filepath)
    ledger.report()
    if show:
        ledger.show()
    return ledger


def get_filepath(args=None):
    args = args if args is not None else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        dest="filepath",
        type=str,
        help="csv file with transaction detail",
        default="data/sample.csv",
    )
    args = parser.parse_args(args)
    return args.filepath


def set_up_logging():
    with open("log/conf.yaml") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)


def main():
    set_up_logging()
    try:
        logger.debug("Begin.")
        filepath = get_filepath()
        sys.exit(get_report(filepath))
    finally:
        logger.debug("Done.")


if __name__ == "__main__":
    main()
