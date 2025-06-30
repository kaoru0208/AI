#!/usr/bin/env python3
import pandas as pd, numpy as np, tensorflow as tf, pickle

SEQ = 50
df  = pd.read_csv("features.csv").reset_index(drop=True)
X_cols = ["close","MA_20","MA_60","RSI_14","BB_upper","BB_lower"]
y_true = df["y_ret"].iloc[SEQ:].values

scaler = pickle.load(open("scaler.pkl","rb"))
X = scaler.transform(df[X_cols])
X_seq = np.array([X[i:i+SEQ] for i in range(len(X)-SEQ)])

model = tf.keras.models.load_model("lstm_fx.h5")
proba = model.predict(X_seq, verbose=0).flatten()
signal = np.where(proba > 0.55, 1, np.where(proba < 0.45, -1, 0))

rets = y_true * signal
equity = np.cumsum(rets)
print(f"最終損益: {equity[-1]*100:.2f}%  |  勝率: {(rets>0).mean():.2%}")
