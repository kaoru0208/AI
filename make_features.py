#!/usr/bin/env python3
import pandas as pd, talib

# --- ① 1分足データを読み込み ---
df = pd.read_csv("candles_USD_JPY_M1.csv", parse_dates=["time"])
df.set_index("time", inplace=True)
df = df.astype(float)

# --- ② テクニカル指標を付与 ---
df["MA_20"]  = talib.SMA(df["close"], 20)
df["MA_60"]  = talib.SMA(df["close"], 60)
df["RSI_14"] = talib.RSI(df["close"], 14)
up, mid, low = talib.BBANDS(df["close"], 20)
df["BB_upper"], df["BB_lower"] = up, low

# --- ③ 教師ラベル（1本先のリターン） ---
df["y_ret"] = df["close"].pct_change().shift(-1)

# --- ④ 欠損除去 & 保存 ---
df.dropna(inplace=True)
df.to_csv("features.csv")
print("features.csv を保存しました。行数=", len(df))
