#!/usr/bin/env python3
import pandas as pd, numpy as np, tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle

SEQ = 50
df  = pd.read_csv("features.csv").reset_index(drop=True)
X_cols = ["close","MA_20","MA_60","RSI_14","BB_upper","BB_lower"]
y = (df["y_ret"] > 0).astype(int)
X = df[X_cols].values

scaler = StandardScaler()
X = scaler.fit_transform(X)

X_seq, y_seq = [], []
for i in range(len(X)-SEQ):
    X_seq.append(X[i:i+SEQ])
    y_seq.append(y.iloc[i+SEQ])
X_seq, y_seq = np.array(X_seq), np.array(y_seq)

X_tr, X_val, y_tr, y_val = train_test_split(
        X_seq, y_seq, test_size=0.2, shuffle=False)

model = tf.keras.Sequential([
    tf.keras.layers.LSTM(64, return_sequences=True, input_shape=X_seq.shape[1:]),
    tf.keras.layers.LSTM(32),
    tf.keras.layers.Dense(1, activation="sigmoid")
])
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.fit(X_tr, y_tr, epochs=15, batch_size=64,
          validation_data=(X_val, y_val))

model.save("lstm_fx.h5")
pickle.dump(scaler, open("scaler.pkl","wb"))
print("lstm_fx.h5 と scaler.pkl を保存しました。")
