#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========= 依存ライブラリ =========
import os, time, datetime as dt
import numpy as np
import pandas as pd
import pickle
from pathlib import Path

from dotenv import load_dotenv
import tensorflow as tf          # tf‑2.16 + keras‑3 用
import talib
import oandapyV20
import oandapyV20.endpoints.instruments as ins
import oandapyV20.endpoints.orders      as ord

load_dotenv()                    # .env からトークンなどを読み込む

# ========= モデル / スケーラの読み込み =========
BASE_DIR   = Path(__file__).resolve().parent           # ~/projects/fxbot
MODEL_DIR  = BASE_DIR / "lstm_fx_saved"                # SavedModel フォルダ
SCALER_PKL = BASE_DIR / "scaler.pkl"                   # 学習時に保存した scaler

model  = tf.keras.models.load_model(MODEL_DIR, compile=False)
scaler = pickle.load(open(SCALER_PKL, "rb"))

# ========= ここから下は**元のコード**をそのまま残す =========

closes=[]; position=0

def latest_close():
    r=ins.InstrumentsCandles(PAIR,params={"count":1,"granularity":GRAN,"price":"M"})
    c=api.request(r)["candles"][0]; return float(c["mid"]["c"])

def features(series):
    close=np.array(series,dtype=float)
    ma20=talib.SMA(close,20)[-1]; ma60=talib.SMA(close,60)[-1]
    rsi=talib.RSI(close,14)[-1]; up,mid,low=talib.BBANDS(close,20)
    return [close[-1],ma20,ma60,rsi,up[-1],low[-1]]

def order(units):
    data={"order":{"instrument":PAIR,"units":str(units),
          "type":"MARKET","timeInForce":"FOK","positionFill":"DEFAULT"}}
    api.request(ord.OrderCreate(ACC,data=data))

while True:
    c=latest_close(); closes.append(c)
    if len(closes)<60: time.sleep(60); continue
    if len(closes)>200: closes=closes[-200:]

    X=scaler.transform([features(closes)])
    X_seq=np.array([np.vstack([X]*SEQ)])
    p=model.predict(X_seq,verbose=0)[0,0]

    now=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if p>THRESH_BUY and position<=0:
        if position<0: order(+UNITS)
        order(+UNITS); position=1; print(now,"BUY ",p)
    elif p<THRESH_SELL and position>=0:
        if position>0: order(-UNITS)
        order(-UNITS); position=-1; print(now,"SELL",p)
    else:
        print(now,"HOLD",p)
    time.sleep(60)
