#!/usr/bin/env python3
import pandas as pd, pathlib, datetime
log=pathlib.Path.home()/ "fxbot_log.csv"
df=pd.read_csv(log,header=None,
      names=["time","prob","vol","sig","units"])
df["time"]=pd.to_datetime(df["time"])
df=df[df["time"]>df["time"].max()-pd.Timedelta(days=30)]
print("30‑day trade count =", (df["sig"]!="WAIT").sum())
print(df.groupby("sig")["sig"].count())
df.to_csv(pathlib.Path.home()/f"fxbot_report_{datetime.date.today()}.csv",index=False)
print("✔ CSV exported")
