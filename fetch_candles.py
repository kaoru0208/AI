#!/usr/bin/env python3
import pandas as pd, numpy as np
from tensorflow import keras

df = pd.read_csv("data_USD_JPY_M5.csv")
price = df["close"].astype(float).values
model = keras.models.load_model("model.h5")

balance, pos, entry = 100000.0, 0, 0.0
for i in range(1, len(price)):
    p_up = model.predict(np.array([[price[i-1]]]), verbose=0)[0][0]
    p    = price[i]
    if p_up > 0.55 and pos==0:         # BUY
        pos, entry = 1000, p
    elif p_up < 0.45 and pos>0:        # CLOSE
        balance += (p-entry)*pos; pos=0
if pos: balance += (price[-1]-entry)*pos
print(f"Final balance: {balance:.2f}")

