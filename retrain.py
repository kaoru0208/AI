#!/usr/bin/env python3
import datetime, numpy as np, pandas as pd, tensorflow as tf, pathlib, os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles

ACC=os.getenv("ACC"); TOK=os.getenv("TOK")
api=oandapyV20.API(access_token=TOK, environment="practice")
PAIR, GRAN, DAYS = "USD_JPY", "M1", 15

def fetch():
    end = pd.Timestamp.utcnow()
    rows=[]
    while len(rows) < DAYS*1440:
        frm = (end - pd.Timedelta(hours=24)).isoformat()
        r = InstrumentsCandles(instrument=PAIR,
              params={"granularity": GRAN, "from": frm, "to": end.isoformat(), "price": "M"})
        api.request(r); rows.extend(r.response["candles"]); end -= pd.Timedelta(hours=24)
    close = np.array([float(c["mid"]["c"]) for c in rows][-DAYS*1440:])
    x = (close - close.mean()) / (close.std()+1e-6)
    X = np.stack([x[i:i+60] for i in range(len(x)-60)], 0)[...,None]
    y = (close[60:] > close[:-60]).astype("float32")
    return X.astype("float32"), y

X,y=fetch()
model=tf.keras.Sequential([
    tf.keras.layers.LSTM(32, input_shape=(60,1)),
    tf.keras.layers.Dense(1, activation="sigmoid")])
model.compile("adam","binary_crossentropy")
model.fit(X,y,epochs=3,batch_size=512,verbose=2)
model.save(str(pathlib.Path.home()/ "projects/fxbot/lstm_fx.h5"))
print("✔ retrained", datetime.datetime.utcnow())
