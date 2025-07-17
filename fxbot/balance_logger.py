from __future__ import annotations
from pathlib import Path
import csv
import datetime as dt

BALANCE_LOG = Path("balance_log.csv")


def log_balance(balance: float) -> None:
    """UTC 時刻と残高を 1 行追記する。"""
    with BALANCE_LOG.open("a", newline="") as f:
        csv.writer(f).writerow([dt.datetime.utcnow().isoformat(), balance])
    print("Logged", balance)


if __name__ == "__main__":
    # 使い方:  python fxbot/balance_logger.py 123.45
    import sys

    bal = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    log_balance(bal)
