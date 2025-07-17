#!/usr/bin/env python3
import datetime as dt
import json
import os

import pandas as pd
import yfinance as yf
from apscheduler.schedulers.blocking import BlockingScheduler

PARAMS = (
    json.load(open("best_params.json"))
    if os.path.exists("best_params.json")
    else {"fast": 20, "slow": 53}
)
SYMBOL = "USDJPY=X"


def calc_pos():
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=PARAMS["slow"] * 3)
    df = yf.download(SYMBOL, start=start, end=end, progress=False, auto_adjust=True)
    ema_f = df["Close"].ewm(span=PARAMS["fast"]).mean()
    ema_s = df["Close"].ewm(span=PARAMS["slow"]).mean()
    pos = 1 if ema_f.iat[-1] > ema_s.iat[-1] else -1
    today = end.date()
    pd.DataFrame(
        [[today, pos, PARAMS["fast"], PARAMS["slow"]]],
        columns=["date", "pos", "fast", "slow"],
    ).to_csv(
        "signals.csv", mode="a", header=not os.path.exists("signals.csv"), index=False
    )
    print(f"{today} → position={pos}")


sched = BlockingScheduler(timezone="Asia/Tokyo")
sched.add_job(calc_pos, "cron", hour=6, minute=5)
print("⏰ Scheduler started (Asia/Tokyo 06:05)… Ctrl‑C で停止")
sched.start()
